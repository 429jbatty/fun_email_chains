import datetime

from AOTW.logic.config import Config
from AOTW.logic.communications import FormAPI
from AOTW.logic.form_manager import FormManager
from AOTW.logic.aotw_manager import AOTWManager
from AOTW.logic.group import Group
from AOTW.logic.date_helper import DateHelper


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


if __name__ == "__main__":
    env = "prod"
    test_date = None
    # test_date = datetime.datetime.strptime("2024-10-28", "%Y-%m-%d")
    search_for_new_aotw(env, test_date)
