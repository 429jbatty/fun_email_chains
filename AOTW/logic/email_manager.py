from AOTW.logic.config import Env


class EmailManager:
    def __init__(self, config, emailer):
        self.config = config
        self.emailer = emailer
        self.send_email_func = (
            emailer.send_email
            if self.config.env == Env.PROD
            else EmailManager._print_email_to_terminal
        )

    def send_aotw_email(self, chooser_name):
        subject = "New AOTW!"

        body = f"""Time for a new AOTW! It is {chooser_name}'s turn to choose an album.\n\nPlease submit your AOTW here: {self.config.aotw_form_link}\n\nHere's the playlist: {self.config.playlist_link}"""

        self.send_email_func(self.config.get_participant_emails(), subject, body)

    def send_reminder_email(self, days_left: int):
        subject = f"AOTW Reminder - {days_left} Days Left to Listen"
        body = (
            f"Remember to listen to the AOTW! You have {days_left} days left to listen."
        )
        self.send_email_func(self.config.get_participant_emails(), subject, body)

    def _print_email_to_terminal(recipients, subject, body):
        print(f"**MOCK EMAIL**")
        print(f"Recipients:{recipients}")
        print(f"Subject:{subject}")
        print(f"\n{body}")
