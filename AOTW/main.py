import datetime

from config import Config
from communications import GmailAPI
from spotify import SpotifyClient
from email_manager import EmailManager
from aotw_manager import AOTWManager
from playlist_manager import PlaylistManager
from group import Group
from date_helper import DateHelper

def daily_email(env, test_date:datetime.datetime=None):
    config = Config(env, test_date)
    group = Group([*config.get_participant_emails()])
    date_helper = DateHelper(config.get_test_date())
    email_manager = EmailManager(config, GmailAPI(config.get_sender_email()))
    manager = AOTWManager(config, group, date_helper, email_manager)
    manager.run_daily_task()

def update_playlist(env, test_date:datetime.datetime=None):
    config = Config(env, test_date)
    group = Group([*config.get_participant_emails()])
    date_helper = DateHelper(config.get_test_date())
    email_manager = EmailManager(config, GmailAPI(config.get_sender_email()))
    playlist_manager = PlaylistManager(SpotifyClient)
    manager = AOTWManager(config, group, date_helper, email_manager, playlist_manager)
    
    manager.update_playlist() 

if __name__ == "__main__":
    env = "test"
    test_date = datetime.datetime.strptime("2024-10-28", "%Y-%m-%d")
    # daily_email(env, test_date)
    update_playlist(env, test_date)