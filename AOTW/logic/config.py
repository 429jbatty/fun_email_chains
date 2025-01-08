import os
import datetime
from enum import Enum
from dotenv import load_dotenv
import pytz
from google.cloud import secretmanager
import json

from AOTW.logic.date_helper import DateHelper
from AOTW.logic.communications import CredentialsManager


class Env(Enum):
    TEST = "test"
    PROD = "prod"


class Config:
    def __init__(self, env, test_date: datetime.datetime = None):
        self.env = self._get_env(env)
        self.run_date = self._get_run_date(test_date)
        self.project_id = self._get_run_var("PROJECT_ID")
        self.bot_email = self._get_run_var("SENDER_EMAIL")
        self.spotify_local_credentials = self._get_spotify_local_credentials()
        self.participant_emails = self._get_run_var("PARTICIPANT_EMAILS").split(",")
        self.aotw_day = self._get_run_var("AOTW_DAY")
        self.aotw_form_link = self._get_run_var("AOTW_FORM_LINK")
        self.aotw_form_id = self._get_run_var("AOTW_FORM_ID")
        self.playlist_id = self._get_run_var("PLAYLIST_ID")
        self.playlist_link = self._get_run_var("PLAYLIST_LINK")
        self.openai_api_key = self._get_run_var("OPENAI_API_KEY")
        self.reminder_days = self._get_run_var("REMINDER_DAYS").split(",")
        self.package_path = os.path.dirname(os.path.dirname(__file__))
        self._print_config_to_terminal()

    @property
    def current_week(self):
        return DateHelper(self.run_date).get_current_week(
            reference_day_of_week=self.get_aotw_day_as_int()
        )

    @property
    def album_log_filepath(self):
        if self.env == Env.PROD:
            return f"albums/aotw_{self.current_week}.json"
        else:
            return f"albums/test/aotw_{self.current_week}.json"

    def _get_env(self, env):
        result = Env(env)
        return result

    def _load_local_env(self):
        result = load_dotenv()
        if result == False:
            raise Exception("Could not find .env")

    def _get_run_var(self, var_name: str):
        """Returns environment variable value.

        If GOOGLE_APPLICATION_CREDENTIALS is set (indicating GCP), it will use Google Cloud Secret Manager.
        Otherwise, it will search for the variable in the .env file.

        Args:
            var_name (str): environment variable name

        Returns:
            str: variable value
        """
        try:
            self._load_local_env()

            if self.env == Env.TEST:
                # local dev variables
                dev_var_name = f"DEV_{var_name}"
                value = os.environ.get(dev_var_name)
                if value is None:
                    pass
                else:
                    return value
            # local prod variables
            return os.environ.get(var_name)
        except:
            if self.env == Env.TEST:
                # GCP dev variables
                dev_var_name = f"DEV_{var_name}"
                try:
                    return CredentialsManager().get_secret_value(dev_var_name)
                except:
                    return CredentialsManager().get_secret_value(var_name)
            return CredentialsManager().get_secret_value(var_name)

    def _read_json_file(self, path):
        try:
            with open(path, "r") as f:
                json_data = json.load(f)
            return json_data
        except:
            raise Exception("Error reading json data")

    def _get_spotify_local_credentials(self):
        try:
            return self._read_json_file(self._get_run_var("SPOTIFY_CREDENTIALS_FILE"))
        except:
            print("Did not find local spotify credentials")

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
