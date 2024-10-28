from date_helper import DateHelper
from album import Album

class EmailManager:
    def __init__(self, config, emailer):
        self.config = config
        self.emailer = emailer
        self.send_email_func = emailer.send_email if self.config.env.is_prod() else EmailManager._print_email_to_terminal

    def send_aotw_email(self, chooser_name):
        subject = self.config.new_aotw_email_subject
        body = f"Time for a new AOTW! It is {chooser_name}'s turn to choose an album."
        self.send_email_func(self.config.get_participant_emails(), subject, body)

    def send_reminder_email(self, days_left:int):
        subject = f"AOTW Reminder - {days_left} Days Left to Listen"
        body = f"Remember to listen to the AOTW! You have {days_left} days left to listen."
        self.send_email_func(self.config.get_participant_emails(), subject, body)

    def send_aotw_follow_up(self):
        pass

    def _print_email_to_terminal(recipients, subject, body):
        print(f"**MOCK EMAIL**")
        print(f"Recipients:{recipients}")
        print(f"Subject:{subject}")
        print(f"\n{body}")

    def _parse_aotw_submission(self, email_body:str)->Album:
        return Album("Either/Or", "Eliot Smith", None)

    def retrieve_aotw_submission(self, expected_sender:str):
        submission = self.emailer.find_latest_aotw_submission(
            expected_sender, 
            self.config.new_aotw_email_subject
        )
        if submission is None:
            return None
        try:
            return self._parse_aotw_submission(submission)
        except:
            print("AOTW submission was received but could not be parsed")
            return None # TODO
        
