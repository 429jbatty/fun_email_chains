import datetime

from AOTW.logic.config import Config
from AOTW.logic.communications import GmailAPI
from AOTW.logic.email_manager import EmailManager
from AOTW.logic.aotw_manager import AOTWManager
from AOTW.logic.group import Group
from AOTW.logic.date_helper import DateHelper


def daily_email(env, test_date: datetime.datetime = None):
    config = Config(env, test_date)
    group = Group([*config.get_participant_emails()])
    date_helper = DateHelper(config.run_date)
    email_manager = EmailManager(config, GmailAPI(config.get_sender_email()))
    manager = AOTWManager(
        config=config, group=group, date_helper=date_helper, email_manager=email_manager
    )

    manager.send_daily_email()


if __name__ == "__main__":
    env = "prod"
    test_date = None
    # test_date = datetime.datetime.strptime("2024-10-28", "%Y-%m-%d")
    daily_email(env, test_date)
