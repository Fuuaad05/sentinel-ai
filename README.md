# Sentinel — AWS Build Week

**Sentinel** is an early-access registration website for a proposed AI-agent security checkpoint. The interactive demo is a **static, rule-based illustration**. It does not connect to, analyze, or protect real AI agents.

## Architecture

Browser → AWS Amplify Hosting → API Gateway HTTP API → AWS Lambda → Amazon DynamoDB + Amazon SES.

The supplied AWS SAM template deploys **API Gateway, Lambda, DynamoDB, and IAM permissions**. Static site hosting is a separate deployment step (Amplify Hosting is easiest, or use a private S3 bucket with CloudFront Origin Access Control).

## Requirements

- AWS account with billing access and AWS CLI/SAM CLI configured locally.
- An AWS region with SES access and a verified SES sender identity.
- A deployed HTTPS static site origin to restrict CORS.
- Python 3.12 for local tests (AWS Lambda uses Python 3.12).

## Deploy

1. Set an AWS Budget alert before deploying. Never publish AWS access keys.
2. Deploy `site/` as a static website via AWS Amplify Hosting or S3 + CloudFront. It will display a clear 'not connected yet' message until the API URL is set.
3. In the **same AWS region** as your SAM stack, verify the sender address in SES. In SES sandbox, **recipient addresses must also be verified**; request production access if you need to email unverified recipients. Production access is not guaranteed or instantaneous.
4. From the repository root, run:

   ```bash
   sam build --template-file infra/template.yaml
   sam deploy --guided --capabilities CAPABILITY_IAM
   ```

   For parameters, set `SenderEmail` to your verified SES address and `AllowedOrigin` to the exact `https://...` website origin (no path or trailing slash). Review IAM permissions and cost before confirming deployment.
5. Copy the `SignupEndpoint` stack output into `site/config.js`:

   ```js
   window.SENTINEL_CONFIG = { apiUrl: 'https://YOUR_API_ID.execute-api.YOUR_REGION.amazonaws.com/join' };
   ```

6. Republish the static site. Test from its live HTTPS URL.

## Testing checklist

- [ ] Mobile and desktop responsive layout
- [ ] All three rule-based simulations show correct decisions
- [ ] Invalid name/email rejected in browser and backend
- [ ] New signup creates DynamoDB record
- [ ] Repeat signup does not create a second record
- [ ] SES confirmation email delivered to a verified recipient (while sandboxed)
- [ ] CORS only permits the configured website origin
- [ ] API errors display without breaking the UI

## Important limitations / production hardening

This is a showcase MVP, not a production-ready public mailing-list service. The deployed API has basic API Gateway throttling (2 requests/second, burst 5), configured manually rather than through the SAM template. A honeypot field and a 4 KB request-body limit provide additional basic protections. These controls do not prevent all automated abuse. The project still lacks consent logging, verified-email opt-in, unsubscribe automation, a data-retention/deletion workflow, and monitoring/alarms. Before production use, consider AWS WAF and stronger abuse protection, an email-verification/opt-in workflow, a privacy notice with a real contact, and a compliant unsubscribe process. The form currently claims only occasional project updates; do not send marketing email without proper consent. The Lambda uses a DynamoDB conditional write to avoid duplicates. If SES fails after a record is stored, retrying the same signup will not resend an email; a production implementation needs a delivery queue and retry mechanism. SES send permissions are region/account dependent.

## Demo outline (90 seconds)

1. Explain the risk: AI agents can access tools and data.
2. Show the three illustrative scenarios (allow, require approval, block).
3. Submit a test email and show the success response.
4. Show the DynamoDB record and SES test email.
5. Explain API Gateway → Lambda → DynamoDB/SES architecture, and identify the simulation as a concept demo.

## Cleanup

Delete the SAM stack with `sam delete` and remove any separately deployed hosting resources when finished. Review billing and budget alerts.
