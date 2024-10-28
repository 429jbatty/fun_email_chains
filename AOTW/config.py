import os
import datetime
from date_helper import DateHelper

class Env:
    TEST = "test"
    PROD = "prod"

    def __init__(self, env):
        self.env = env.lower()

    def is_test(self):
        return self.env == self.TEST

    def is_prod(self):
        return self.env == self.PROD

class Config:
    def __init__(self, env, test_date:datetime.datetime=None):
        self.env = Env(env)
        self.test_date = test_date
        self.bot_email = os.environ.get("SENDER_EMAIL")
        self.participant_emails = os.environ.get("PARTICIPANT_EMAILS").split(",")
        self.aotw_day = os.environ.get("AOTW_DAY")
        self.data_folder = os.environ.get("DATA_FOLDER")
        self.reminder_days = os.environ.get("REMINDER_DAYS").split(",")
        self.new_aotw_email_subject = os.environ.get("AOTW_EMAIL_SUBJECT")
        self.package_path = os.path.dirname(__file__)
 
    def get_sender_email(self):
        return self.bot_email

    def get_participant_emails(self):
        return self.participant_emails

    def get_test_date(self):
        if self.env.is_prod and self.test_date is not None:
            return self.test_date

    def get_aotw_day_as_int(self):
        try:
            return DateHelper.string_day_to_int(self.aotw_day)
        except ValueError:
            raise ValueError(f"Invalid AOTW_DAY: {self.aotw_day}. Must be a valid day of the week, e.g., 'Monday', 'Tuesday'.")

    def get_reminder_days_as_int(self):
        try:
            return [DateHelper.string_day_to_int(day) for day in self.reminder_days]
        except ValueError:
            raise ValueError(f"Invalid AOTW_DAY: {self.aotw_day}. Must be a valid day of the week, e.g., 'Monday', 'Tuesday'.")