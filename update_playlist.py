import datetime

from AOTW.logic.config import Config
from AOTW.logic.communications import SpotifyAPI
from AOTW.logic.aotw_manager import AOTWManager
from AOTW.logic.playlist_manager import PlaylistManager
from AOTW.logic.group import Group
from AOTW.logic.date_helper import DateHelper


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


if __name__ == "__main__":
    env = "prod"
    test_date = None
    # test_date = datetime.datetime.strptime("2024-10-28", "%Y-%m-%d")
    update_playlist(env, test_date)
