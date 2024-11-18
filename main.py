import datetime

from AOTW.logic.config import Config
from AOTW.logic.communications import FormAPI
from AOTW.logic.form_manager import FormManager
from AOTW.logic.aotw_manager import AOTWManager
from AOTW.logic.group import Group
from AOTW.logic.date_helper import DateHelper
from AOTW.logic.email_manager import EmailManager
from AOTW.logic.communications import GmailAPI, SpotifyAPI
from AOTW.logic.playlist_manager import PlaylistManager


def daily_email(env, test_date: datetime.datetime = None):
    config = Config(env, test_date)
    group = Group([*config.get_participant_emails()])
    date_helper = DateHelper(config.run_date)
    email_manager = EmailManager(config, GmailAPI(config.get_sender_email()))
    manager = AOTWManager(
        config=config, group=group, date_helper=date_helper, email_manager=email_manager
    )

    manager.send_daily_email()


def search_for_new_aotw(env, test_date: datetime.datetime = None):
    config = Config(env, test_date)
    date_helper = DateHelper(config.run_date)
    form_manager = FormManager(config, FormAPI())
    group = Group([*config.get_participant_emails()])
    manager = AOTWManager(
        config=config, date_helper=date_helper, form_manager=form_manager, group=group
    )

    manager.retrieve_and_log_form_submissions()
    manager.create_aotw_weekly_file()


def update_playlist(env, test_date: datetime.datetime = None):
    config = Config(env, test_date)
    date_helper = DateHelper(config.run_date)
    group = Group([*config.get_participant_emails()])
    playlist_manager = PlaylistManager(config, SpotifyAPI())
    manager = AOTWManager(
        config=config,
        date_helper=date_helper,
        playlist_manager=playlist_manager,
        group=group,
    )

    manager.update_playlist()
