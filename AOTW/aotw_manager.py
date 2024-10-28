import os
import json

from date_helper import DateHelper
from album import Album
from group import Group
from email_manager import EmailManager
from playlist_manager import PlaylistManager
from config import Config

class AOTWManager:
    def __init__(
            self, 
            config:Config,
            group:Group=None, 
            date_helper:DateHelper=None, 
            email_manager:EmailManager=None, 
            playlist_manager:PlaylistManager=None 
        ):
        self.group = group
        self.date_helper = date_helper
        self.email_manager = email_manager
        self.playlist_manager = playlist_manager
        self.config = config
        self.chooser = self._get_current_chooser()
        self.aotw = self._get_current_aotw()
        self.is_playlist_updated = self._is_playlist_updated()
        self.today_as_int = self.date_helper.get_current_weekday()
        self.aotw_day_as_int = self.config.get_aotw_day_as_int()
        self.reminder_days_as_ints = self.config.get_reminder_days_as_int()

    def _get_current_chooser(self):
        current_week = self.date_helper.get_current_week(reference_day_of_week=self.config.get_aotw_day_as_int())
        chooser_index = current_week % len(self.group.participants)
        return self.group.participants[chooser_index]

    def _read_aotw_from_log(self):
        current_week = self.date_helper.get_current_week(reference_day_of_week=self.config.get_aotw_day_as_int())
        filepath = os.path.join(os.path.join(self.config.package_path, self.config.data_folder), f"aotw_{current_week}.json")
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                json_data = json.load(f)
                return Album(**json_data)
        else:
            return None

    def _get_current_aotw(self):
        aotw = self._read_aotw_from_log()
        if aotw is not None:
            return aotw
        else:
            aotw = self.email_manager.retrieve_aotw_submission(
                expected_sender=self.chooser.email
            )
            if aotw is not None:
                current_week = self.date_helper.get_current_week(reference_day_of_week=self.config.get_aotw_day_as_int())
                aotw.week = current_week
                aotw.log_data(current_week)                
            else:
                print("AOTW for this week has not been submitted!")
                return None
            
    def _is_playlist_updated(self):
        if self.aotw is None:
            return False
        else:
            return self.aotw.playlist_updated
            
    def update_playlist(self):
        if self.aotw is not None:
            if self.is_playlist_updated:
                print("Spotify playlist is up-to-date")
            else:
                print("Updating spotify playlist...")
                self.playlist_manager.update_playlist()
                self.aotw.playlist_updated = True
                self.aotw.log_data()
                print("Playlist updated")
        else:
            print("There is currently no AOTW!")

    def run_daily_task(self):
        if self.today_as_int == self.aotw_day_as_int:
            print("Sending AOTW email")
            self.email_manager.send_aotw_email(self.chooser.name)
        elif self.today_as_int in self.reminder_days_as_ints:
            if self.aotw is None:
                return print("There is still no AOTW!")
            print("Sending reminder email")
            days_left = DateHelper.days_between_weekday_ints(self.today_as_int,self.aotw_day_as_int)
            self.email_manager.send_reminder_email(days_left=days_left)
        else:
            print("No email to send today")
