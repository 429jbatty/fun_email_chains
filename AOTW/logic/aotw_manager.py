import os
import json
import datetime
import pytz

from AOTW.logic.date_helper import DateHelper
from AOTW.logic.album import Album
from AOTW.logic.group import Group
from AOTW.logic.email_manager import EmailManager
from AOTW.logic.playlist_manager import PlaylistManager
from AOTW.logic.form_manager import FormManager
from AOTW.logic.config import Config


class AOTWManager:
    def __init__(
        self,
        config: Config,
        group: Group = None,
        date_helper: DateHelper = None,
        email_manager: EmailManager = None,
        playlist_manager: PlaylistManager = None,
        form_manager: FormManager = None,
    ):
        self.group = group
        self.date_helper = date_helper
        self.email_manager = email_manager
        self.playlist_manager = playlist_manager
        self.form_manager = form_manager
        self.config = config
        self.chooser = self._get_current_chooser()
        self.today_as_int = self.date_helper.get_current_weekday()
        self.aotw_day_as_int = self.config.get_aotw_day_as_int()
        self.reminder_days_as_ints = self.config.get_reminder_days_as_int()

    def _get_current_chooser(self):
        current_week = self.date_helper.get_current_week(
            reference_day_of_week=self.config.get_aotw_day_as_int()
        )
        chooser_index = current_week % len(self.group.participants)
        return self.group.participants[chooser_index]

    def _is_playlist_updated(self):
        aotw = self.get_aotw()
        if self.get_aotw() is None:
            return False
        else:
            return aotw.playlist_updated

    def _read_aotw_from_log(
        self,
    ):
        current_week = self.date_helper.get_current_week(
            reference_day_of_week=self.config.get_aotw_day_as_int()
        )

        filepath = os.path.join(
            os.path.join(self.config.package_path, self.config.data_folder),
            f"aotw_{current_week}.json",
        )
        if os.path.exists(filepath):
            with open(filepath, "r") as f:
                json_data = json.load(f)
                return Album(**json_data)
        else:
            print(f"No log file found for week {current_week}")
            return None

    def create_aotw_weekly_file(self):
        with open("AOTW/data/submissions.json", "r") as f:
            submission_data = json.load(f)

        filtered_data = [
            entry
            for entry in submission_data
            if entry["user_email"] == self.chooser.email
        ]
        filtered_data = [
            entry
            for entry in filtered_data
            if datetime.datetime.fromisoformat(entry["timestamp"])
            >= self.date_helper.get_start_of_aotw(self.aotw_day_as_int).replace(
                tzinfo=pytz.UTC
            )
            and datetime.datetime.fromisoformat(entry["timestamp"])
            <= self.date_helper.get_end_of_aotw(self.aotw_day_as_int).replace(
                tzinfo=pytz.UTC
            )
        ]

        # Sort by timestamp in descending order (most recent first)
        filtered_data.sort(key=lambda entry: entry["timestamp"], reverse=True)

        # Return the first element (most recent) if any
        if filtered_data:
            relevant_submission = filtered_data[0]
            aotw = Album(**relevant_submission)
            aotw._set_week(self.date_helper.get_current_week(self.aotw_day_as_int))
            aotw.log_data()

    def retrieve_and_log_form_submissions(self):
        return self.form_manager.retrieve_and_log_submissions()

    def update_playlist(self):
        aotw = self._read_aotw_from_log()
        if aotw is not None:
            if aotw.playlist_updated:
                print("Spotify playlist is up-to-date")
            else:
                print("Updating spotify playlist...")
                self.playlist_manager.update_playlist(aotw)
                aotw.playlist_updated = True
                aotw.log_data()
        else:
            print("Cannot update playlist because there is currently no AOTW!")
            print(f"Tell {self.chooser.name} to get on it!")

    def send_daily_email(self):
        if self.today_as_int == self.aotw_day_as_int:
            print("Sending AOTW email")
            self.email_manager.send_aotw_email(self.chooser.name)
        elif self.today_as_int in self.reminder_days_as_ints:
            if self._read_aotw_from_log() is None:
                return print("Cannot send reminder because AOTW was not picked")
            print("Sending reminder email")
            days_left = DateHelper.days_between_weekday_ints(
                self.today_as_int, self.aotw_day_as_int
            )
            self.email_manager.send_reminder_email(days_left=days_left)
        else:
            print("No email to send today")
