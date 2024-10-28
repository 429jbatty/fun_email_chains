import os
import datetime

class DateHelper:

    def __init__(self, test_date:datetime.datetime=None):
        self.test_date = test_date

    def get_current_day(self):
        if self.test_date is not None:
            if isinstance(self.test_date, datetime.datetime):
                return self.test_date.date()
            else:
                return datetime.datetime.strptime(self.test_date, '%Y-%m-%d').date()
        return datetime.date.today()
    
    def get_current_weekday(self):
        return self.get_current_day().weekday()      
    
    def get_current_week(self, reference_day_of_week: int):
        """
        Calculates the number of a specific day of the week that have occurred in the year so far, up to the current date.

        Args:
            reference_day_of_week: The day of the week as an integer (0 for Monday, 6 for Sunday).

        Returns:
            The number of the specified day of the week that have occurred so far in the year.
        """

        today = self.get_current_day()

        start_of_year = datetime.date(today.year, 1, 1)
        days_since_start = (today - start_of_year).days + 1

        # Find the first occurrence of the specified day of the week within those days
        first_day_index = (reference_day_of_week - start_of_year.weekday()) % 7

        # Calculate the number of occurrences of the day of the week
        num_occurrences = days_since_start // 7

        # If the current day matches or falls after the first occurrence, count it as an additional occurrence
        if days_since_start >= first_day_index:
            num_occurrences += 1

        return num_occurrences 

    def string_day_to_int(day):
        """Converts a list of string representations of days of the week to a list of integer representations.

        Args:
            days: A list of strings representing days of the week (e.g., ["Monday", "Wednesday", "Friday"]).

        Returns:
            A list of integers representing the days of the week (e.g., [0, 2, 4]).
        """

        day_map = {
            "Monday": 0,
            "Tuesday": 1,
            "Wednesday": 2,
            "Thursday": 3,
            "Friday": 4,
            "Saturday": 5,
            "Sunday": 6
        }

        return day_map[day.title()]
    
    def days_between_weekday_ints(weekday_as_int_1, weekday_as_int_2):
        """Calculates the number of days between two weekdays.

        Args:
            weekday1: An integer representing the first weekday (0 for Monday, 6 for Sunday).
            weekday2: An integer representing the second weekday.

        Returns:
            The number of days between the two weekdays.
        """

        return abs((weekday_as_int_2 - weekday_as_int_1) % 7)