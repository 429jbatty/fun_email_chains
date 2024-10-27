import base64
import os
import dotenv

from email.mime.text import MIMEText
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


class GmailAPI:
    """
    A class for interacting with the Gmail API.

    Handles authentication, message creation, and email sending.
    """

    SCOPES = ['https://www.googleapis.com/auth/gmail.send']

    def __init__(self):
        self.service = None
        dotenv.load_dotenv()  # Load environment variables from .env file
        self.SENDER_EMAIL = os.getenv('SENDER_EMAIL')

    def _authenticate(self):
        """
        Authenticates to the Gmail API using OAuth 2.0.

        Returns:
            A Gmail API service object.

        Raises:
            HttpError: If authentication fails.
        """

        creds = None
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', self.SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', self.SCOPES)
                creds = flow.run_local_server(port=0)
            with open('token.json', 'w') as token:
                token.write(creds.to_json())

        try:
            service = build('gmail', 'v1', credentials=creds)
            return service
        except HttpError as error:
            raise

    def create_message(self, sender, to, subject, body):
        """
        Creates a message for an email.

        Args:
            sender: Email address of the sender.
            to: Email address of the recipient.
            subject: Subject of the email.
            body: Email body content.

        Returns:
            A message object encoded in base64url.
        """

        message = MIMEText(body, 'plain')
        message['to'] = to
        message['from'] = sender
        message['subject'] = subject
        return base64.urlsafe_b64encode(message.as_bytes()).decode()


    def send_email(self, recipient, subject, body):
        """
        Sends an email using the Gmail API.

        Args:
            recipient: Email address of the recipient.
            subject: Subject of the email.
            body: Email body content.

        Raises:
            HttpError: If email sending fails.
        """

        if not self.service:
            self.service = self._authenticate()

        try:
            message = self.create_message(self.SENDER_EMAIL, recipient, subject, body)
            self.service.users().messages().send(userId='me', body={'raw': message}).execute()
            print('Email sent!')
        except HttpError as error:
            print(f'An error occurred: {error}')
            raise


# Example usage
if __name__ == '__main__':
    gmail_api = GmailAPI()
    gmail_api.send_email(recipient='429jbatty@gmail.com',
                          subject='Test Email',
                          body='This is a test email.')