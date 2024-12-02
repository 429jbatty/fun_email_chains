import os
import datetime
from enum import Enum
from dotenv import load_dotenv
import pytz

from AOTW.logic.date_helper import DateHelper


class Env(Enum):
    TEST = "test"
    PROD = "prod"


class Config:
    def __init__(self, env, test_date: datetime.datetime = None):
        self.env = self._get_env(env)
        self.run_date = self._get_run_date(test_date)
        self._load_env()
        self.bot_email = self._get_run_var("SENDER_EMAIL")
        self.participant_emails = self._get_run_var("PARTICIPANT_EMAILS").split(",")
        self.aotw_day = self._get_run_var("AOTW_DAY")
        self.aotw_form_link = self._get_run_var("AOTW_FORM_LINK")
        self.aotw_form_id = self._get_run_var("AOTW_FORM_ID")
        self.playlist_id = self._get_run_var("PLAYLIST_ID")
        self.playlist_link = self._get_run_var("PLAYLIST_LINK")
        self.reminder_days = self._get_run_var("REMINDER_DAYS").split(",")
        self.package_path = os.path.dirname(os.path.dirname(__file__))
        self._print_config_to_terminal()

    @property
    def current_week(self):
        return DateHelper(self.run_date).get_current_week(reference_day_of_week=self.get_aotw_day_as_int())

    @property
    def album_log_filepath(self):
        if self.env == Env.PROD:
            return f"albums/aotw_{self.current_week}.json"
        else:
            return f"albums/test/aotw_{self.current_week}.json"

    def _get_env(self, env):
        result = Env(env)
        return result

    def _load_env(self):
        result = load_dotenv()
        if result == False:
            raise Exception("Could not find .env")

    def _get_run_var(self, var_name:str):
        """Returns environment variable value. If env is TEST, will search for "DEV_<variable name>" before default to prod version.

        Args:
            var_name (str): environment variable name

        Returns:
            str: variable value
        """
        if self.env == Env.TEST:
            dev_var_name = f"DEV_{var_name}"
            value = os.environ.get(dev_var_name)
            if value is None:
                pass
            else:
                return value
        return os.environ.get(var_name)

    def _print_config_to_terminal(self):
        print("------------------------------")
        print("RUN PARAMETERS:")
        print(f"Environment: {self.env.name}")
        print(f"Date: {self.run_date}")
        print(f"Participants: {self.participant_emails}")
        print("\n")
        
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
            run_date = datetime.datetime.now(tz=pytz.timezone("US/Pacific")).date()
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

    