class Manager:
    def __init__(self, config, emailer, group, date_helper):
        self.config = config
        self.emailer = emailer
        self.group = group
        self.date_helper = date_helper

    def get_current_participant(self):
        current_week = self.date_helper.get_current_week()
        chooser_index = current_week % len(self.group.participants)
        return self.group.participants[chooser_index]

    def send_sunday_email(self):
        chooser_name = self.get_current_participant().name
        subject = f"New AOTW from {chooser_name}!!!"
        body = f"Time for a new AOTW! It is {chooser_name}'s turn to choose an album."
        self.emailer.send_email(self.config.get_participant_emails(), subject, body)
        # Update turn for next Sunday email
        self.group.next_turn()

    def send_reminder_email(self):
        days_left = 6 - int(self.date_helper.get_current_day())
        subject = f"AOTW Reminder - {days_left} Days Left to Listen"
        body = f"Remember to listen to the AOTW! You have {days_left} days left to listen."
        self.emailer.send_email(self.config.get_participant_emails(), subject, body)

    def send_daily_email(self):

        if self.date_helper.get_current_day() == 6:  # Sunday
            print("Sending sunday email")
            self.send_sunday_email()
        elif self.date_helper.get_current_day() == 4:  # Friday
            print("Sending reminder email")
            self.send_reminder_email()
        else:
            print("No email to send today")
