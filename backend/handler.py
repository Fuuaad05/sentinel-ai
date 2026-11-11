import json
import os
import re
import time
import hashlib
import boto3
from botocore.exceptions import ClientError

TABLE = os.environ.get('TABLE_NAME', '')
SENDER = os.environ.get('SES_SENDER', '')
ORIGIN = os.environ.get('ALLOWED_ORIGIN', '')
ddb = boto3.client('dynamodb')
ses = boto3.client('ses')
EMAIL_RE = re.compile(r'^[^\s@]+@[^\s@]+\.[^\s@]+$')

def reply(code, message):
    return {'statusCode': code, 'headers': {'Content-Type': 'application/json', 'Cache-Control': 'no-store', 'Access-Control-Allow-Origin': ORIGIN}, 'body': json.dumps({'message': message})}

def handler(event, context):
    try:
        raw_body = event.get('body') or '{}'
        if not isinstance(raw_body, str):
            return reply(400, 'Invalid submission.')
        if len(raw_body.encode('utf-8')) > 4096:
            return reply(413, 'Submission is too large.')
        body = json.loads(raw_body)
        if not isinstance(body, dict):
            return reply(400, 'Invalid submission.')
        if body.get('website'):
            return reply(200, 'Thank you for your interest.')
        name = body.get('name', '')
        email = body.get('email', '')
        if not isinstance(name, str) or not isinstance(email, str):
            return reply(400, 'Enter a valid name and email.')
        name = name.strip()
        email = email.strip().lower()
        if not (1 <= len(name) <= 80 and len(email) <= 254 and EMAIL_RE.fullmatch(email)):
            return reply(400, 'Enter a valid name and email.')
    except (ValueError, TypeError):
        return reply(400, 'Invalid submission.')
    # Hashing the email avoids using the address itself as a DynamoDB key.
    subscriber_id = hashlib.sha256(email.encode('utf-8')).hexdigest()
    try:
        ddb.put_item(TableName=TABLE, Item={'subscriber_id': {'S': subscriber_id}, 'email': {'S': email}, 'name': {'S': name}, 'joined_at': {'N': str(int(time.time()))}}, ConditionExpression='attribute_not_exists(subscriber_id)')
    except ddb.exceptions.ConditionalCheckFailedException:
        return reply(200, 'You are already on the list. Thanks for your interest!')
    except ClientError:
        return reply(503, 'Signup is temporarily unavailable. Please try again.')
    try:
        ses.send_email(Source=SENDER, Destination={'ToAddresses': [email]}, Message={'Subject': {'Data': 'Welcome to the Sentinel early-access list'}, 'Body': {'Text': {'Data': f'Hi {name},\n\nThanks for joining the Sentinel early-access list. Sentinel is an AI-agent security concept in development. We will share occasional project updates.\n\n— Sentinel team'}}})
    except ClientError:
        # Signup is stored even if SES cannot deliver; avoid claiming an email was sent.
        return reply(200, 'You are on the waitlist! Confirmation email delivery is currently unavailable.')
    return reply(200, 'You are on the waitlist! Check your inbox for confirmation.')
