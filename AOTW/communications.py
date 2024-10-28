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

    PORT = 57738
    SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

    def __init__(self, sender_email):
        self.service = None
        self.sender_email = sender_email

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
                    'credentials.json', 
                    self.SCOPES,
                    redirect_uri=f"http://localhost:{GmailAPI.PORT}/"  # Replace with your desired port                     
                )
                creds = flow.run_local_server(port=GmailAPI.PORT)
            with open('token.json', 'w') as token:
                token.write(creds.to_json())

        try:
            service = build('gmail', 'v1', credentials=creds)
            return service
        except HttpError as error:
            raise

    def create_message(self, sender, recipients, subject, body):
        """
        Creates a message for an email.

        Args:
            sender: Email address of the sender.
            recipients: List of email addresses of the recipients.
            subject: Subject of the email.
            body: Email body content.

        Returns:
            A message object encoded in base64url.
        """

        message_bytes = (
            f'To: {", ".join(recipients)}\r\n'
            f'From: {sender}\r\n'
            f'Subject: {subject}\r\n\r\n'
            f'{body}'
        ).encode('utf-8')

        return base64.urlsafe_b64encode(message_bytes).decode()

    def send_email(self, recipients, subject, body):
        """
        Sends an email using the Gmail API.

        Args:
            recipients: List of email addresses of the recipients.
            subject: Subject of the email.
            body: Email body content.

        Raises:
            HttpError: If email sending fails.
        """

        if not self.service:
            self.service = self._authenticate()

        try:
            message = self.create_message(self.sender_email, recipients, subject, body)
            self.service.users().messages().send(userId='me', body={'raw': message}).execute()
            print('Email sent!')
        except HttpError as error:
            print(f'An error occurred: {error}')
            raise


    def find_latest_aotw_submission(self, expected_sender:str, subject:str):
        """
        Finds the latest reply to the AOTW request email from the expected sender with the specific subject.

        Args:
            expected_sender: Email address of the user whose turn it is.
            subject: The exact subject of the AOTW request email.

        Returns:
            The latest email object containing a valid AOTW submission, or None if no valid submission is found.
        """

        if not self.service:
            self.service = self._authenticate()

        try:
            # Build search query
            search_query = f'from: "{expected_sender}" subject:"{subject}"'

            # Fetch message list
            response = self.service.users().messages().list(userId='me', q=search_query, maxResults=1).execute()
            message_ids = response['messages'] if 'messages' in response else []

            if not message_ids:
                return None

            message_id = message_ids[0]['id']
            message = self.service.users().messages().get(userId='me', id=message_id).execute()

            # Check if the message is a reply to the AOTW request email
            # (You might need to implement more specific checks based on your email structure)
            payload = message['payload']
            headers = payload['headers']
            is_reply = False
            for header in headers:
                if header['name'] == 'In-Reply-To':
                    is_reply = True
                    break

            if is_reply:
                # Parse the email body to extract AOTW information
                parts = payload['parts']
                for part in parts:
                    if part['mimeType'] == 'text/plain':
                        body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                        extracted_data = body
                        if extracted_data:  # If data is successfully extracted
                            return message
            else:
                return None

        except HttpError as error:
            print(f'An error occurred while fetching AOTW submissions: {error}')
            return None
        
# Example usage
# if __name__ == '__main__':
#     gmail_api = GmailAPI()
#     gmail_api.send_email(
#         recipient='429jbatty@gmail.com',
#         subject='Test Email',
#         body='This is a test email.'
#     )