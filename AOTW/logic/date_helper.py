import datetime


class DateHelper:

    def __init__(self, current_date: datetime.datetime):
        self.current_date = current_date

    def get_current_weekday(self):
        return self.current_date.weekday()

    def get_start_of_aotw(self, aotw_day_as_int):
        """
        Calculates the start date of the most recent AOTW period before the current date, at midnight Pacific time.

        Args:
            aotw_day_as_int: An integer representing the day of the week when the AOTW starts (0 for Monday, 1 for Tuesday, etc.).

        Returns:
            A datetime object representing the start of the most recent AOTW period at midnight Pacific time.
        """

        today = self.current_date
        weekday = today.weekday()

        days_to_subtract = (weekday - aotw_day_as_int) % 7
        start_of_aotw = today - datetime.timedelta(days=days_to_subtract)

        # Set the time to midnight Pacific Time
        start_of_aotw = datetime.datetime.combine(
            start_of_aotw, datetime.time(hour=0, minute=0, second=0, microsecond=0)
        )

        return start_of_aotw

    def get_end_of_aotw(self, aotw_day_as_int):
        end_of_aotw = self.get_start_of_aotw(aotw_day_as_int) + datetime.timedelta(
            weeks=2  # TODO
        )
        return end_of_aotw

    def get_current_week(self, reference_day_of_week: int):
        """
        Calculates the number of a specific day of the week that have occurred in the year so far, up to the current date.

        Args:
            reference_day_of_week: The day of the week as an integer (0 for Monday, 6 for Sunday).

        Returns:
            The number of the specified day of the week that have occurred so far in the year.
        """

        start_of_year = datetime.date(self.current_date.year, 1, 1)
        days_since_start = (self.current_date - start_of_year).days + 1

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
            "Sunday": 6,
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
