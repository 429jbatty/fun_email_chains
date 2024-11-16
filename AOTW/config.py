import os
import datetime
from enum import Enum
from dotenv import load_dotenv

from date_helper import DateHelper


class Env(Enum):
    TEST = "test"
    PROD = "prod"


class Config:
    def __init__(self, env, test_date: datetime.datetime = None):
        self.env = self._get_env(env)
        self.run_date = self._get_run_date(test_date)
        self._load_env()
        self.bot_email = os.environ.get("SENDER_EMAIL")
        self.participant_emails = os.environ.get("PARTICIPANT_EMAILS").split(",")
        self.aotw_day = os.environ.get("AOTW_DAY")
        self.aotw_form_link = os.environ.get("AOTW_FORM_LINK")
        self.aotw_form_id = os.environ.get("AOTW_FORM_ID")
        self.playlist_id = os.environ.get("PLAYLIST_ID")
        self.playlist_link = os.environ.get("PLAYLIST_LINK")
        self.data_folder = os.environ.get("DATA_FOLDER")
        self.reminder_days = os.environ.get("REMINDER_DAYS").split(",")
        self.package_path = os.path.dirname(__file__)

    def _get_env(self, env):
        result = Env(env)
        print(f"Environment: {result.value}\n")
        return result

    def _load_env(self):
        result = load_dotenv()
        if result == False:
            raise Exception("Could not find .env")

    def get_sender_email(self):
        return self.bot_email

    def get_participant_emails(self):
        return self.participant_emails

    def _get_run_date(self, test_date):
        if self.env == Env.TEST and test_date is not None:
            if isinstance(test_date, datetime.datetime):
                run_date = test_date.date()
            else:
                run_date = datetime.datetime.strptime(test_date, "%Y-%m-%d").date()
        else:
            run_date = datetime.date.today()

        print(f"Run Date: {run_date.strftime("%m/%d/%Y")}\n")
        return run_date

    def get_aotw_day_as_int(self):
        try:
            return DateHelper.string_day_to_int(self.aotw_day)
        except ValueError:
            raise ValueError(
                f"Invalid AOTW_DAY: {self.aotw_day}. Must be a valid day of the week, e.g., 'Monday', 'Tuesday'."
            )

    def get_reminder_days_as_int(self):
        try:
            return [DateHelper.string_day_to_int(day) for day in self.reminder_days]
        except ValueError:
            raise ValueError(
                f"Invalid AOTW_DAY: {self.aotw_day}. Must be a valid day of the week, e.g., 'Monday', 'Tuesday'."
            )
