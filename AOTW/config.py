import os

class Config:
    def __init__(self):
        self.bot_email = os.environ.get("GMAIL_USERNAME")
        self.bot_password = os.environ.get("GMAIL_PASSWORD")
        self.participant_emails = os.environ.get("PARTICIPANT_EMAILS").split(",")

    def get_gmail_credentials(self):
        return self.bot_email, self.bot_password

    def get_participant_emails(self):
        return self.participant_emails