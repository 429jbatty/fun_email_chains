from config import Config
from communications import Emailer
from manager import Manager
from group import Group
from date_helper import DateHelper

def main():
    config = Config()
    emailer = Emailer(*config.get_gmail_credentials())
    group = Group([*config.get_participant_emails()])
    date_helper = DateHelper()
    manager = Manager(config, emailer, group, date_helper)

    manager.send_daily_email()

if __name__ == "__main__":
    main()