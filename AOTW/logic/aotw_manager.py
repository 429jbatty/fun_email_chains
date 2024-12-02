import datetime
import pytz

from AOTW.logic.date_helper import DateHelper
from AOTW.logic.album import Album
from AOTW.logic.group import Group
from AOTW.logic.email_manager import EmailManager
from AOTW.logic.playlist_manager import PlaylistManager
from AOTW.logic.form_manager import FormManager
from AOTW.logic.config import Config
from AOTW.logic.communications import GoogleCloudStorage


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

    def _read_aotw_from_log(self):
        blob_name = self.config.album_log_filepath
        gcs_client = GoogleCloudStorage()
        json_data = gcs_client.read_json(blob_name)
        if json_data is not None:
            return Album(**json_data)
        else:
            return None

    def create_aotw_weekly_file(self):
        blob_name = f"form_submissions/submissions.json"
        gcs_client = GoogleCloudStorage()
        submission_data = gcs_client.read_json(blob_name)

        filtered_data = [
            entry
            for entry in submission_data
            if entry["user_email"] == self.chooser.email
        ]
        filtered_data = [
            entry
            for entry in filtered_data
            if datetime.datetime.fromisoformat(
                entry["timestamp"].replace("Z", "+00:00")
            )
            >= self.date_helper.get_start_of_aotw(self.aotw_day_as_int).replace(
                tzinfo=pytz.UTC
            )
            and datetime.datetime.fromisoformat(
                entry["timestamp"].replace("Z", "+00:00")
            )
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
            aotw.log_data(self.config.album_log_filepath)

    def retrieve_and_log_form_submissions(self):
        return self.form_manager.retrieve_and_log_submissions()

    def update_playlist(self):
        aotw = self._read_aotw_from_log()
        if aotw is not None:
            if aotw.playlist_updated:
                print("Spotify playlist is already up-to-date")
            else:
                print("Updating spotify playlist...")
                self.playlist_manager.update_playlist(aotw)
                aotw.playlist_updated = True
                aotw.log_data(self.config.album_log_filepath)
                print("Playlist updated")
        else:
            print("Cannot update playlist because there is currently no AOTW!")
            print(f"Tell {self.chooser.name} to get on it!")

    def send_chosen_email(self):
        aotw = self._read_aotw_from_log()
        if aotw is not None:
            print(f"Sending email to announce new album ({aotw.album} by {aotw.artist})")
            self.email_manager.send_aotw_chosen_email(album=aotw.album, artist=aotw.artist)
            print(f"Sent")

    def send_daily_email(self):
        if self.today_as_int == self.aotw_day_as_int:
            print("Sending AOTW email")
            self.email_manager.send_aotw_email(self.chooser.name)
            print("Sent")
        elif self.today_as_int in self.reminder_days_as_ints:
            if self._read_aotw_from_log() is None:
                return print("Cannot send reminder because AOTW was not picked")
            print("Sending reminder email")
            days_left = DateHelper.days_between_weekday_ints(
                self.today_as_int, self.aotw_day_as_int
            )
            self.email_manager.send_reminder_email(days_left=days_left)
            print("Sent")
        else:
            print("No email to send today")
