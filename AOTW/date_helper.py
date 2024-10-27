import os
import datetime

class DateHelper:
    def get_current_day(self):
        test_day = os.environ.get("TEST_DAY")
        if test_day is not None:
            return int(test_day)
        return datetime.date.today().weekday()
    
    def get_current_week(self):
        return datetime.date.today().isocalendar()[1]    