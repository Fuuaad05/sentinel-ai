import json
import os
import sys
import unittest
from unittest.mock import MagicMock
os.environ.update(TABLE_NAME='test', SES_SENDER='sender@example.com', ALLOWED_ORIGIN='https://example.com')
sys.modules['boto3'] = MagicMock()
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
import handler as app
class HandlerTests(unittest.TestCase):
    def setUp(self):
        app.ddb.reset_mock()
        app.ses.reset_mock()
    def send(self, payload):
        return app.handler({'body': json.dumps(payload)}, None)
    def test_valid_signup(self):
        response = self.send({'name':'Jane', 'email':'Jane@example.com'})
        self.assertEqual(response['statusCode'],200)
        app.ddb.put_item.assert_called_once()
        app.ses.send_email.assert_called_once()

    def test_oversized_request(self):
        import json
        import handler

        event = {
            "body": json.dumps({
                "name": "A" * 5000,
                "email": "test@example.com"
            })
        }

        response = handler.handler(event, None)
        self.assertEqual(response["statusCode"], 413)

    def test_bad_email(self):
        self.assertEqual(self.send({'name':'Jane','email':'invalid'})['statusCode'],400)
        app.ddb.put_item.assert_not_called()
    def test_honeypot(self):
        self.assertEqual(self.send({'name':'Jane','email':'jane@example.com','website':'spam'})['statusCode'],200)
        app.ddb.put_item.assert_not_called()
    def test_invalid_body(self):
        self.assertEqual(app.handler({'body':'{'},None)['statusCode'],400)
if __name__=='__main__':unittest.main()
