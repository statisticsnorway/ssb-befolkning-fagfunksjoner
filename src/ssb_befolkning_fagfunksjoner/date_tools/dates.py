import calendar
from datetime import date

__all__ = [
    "get_last_day_of_month",
    "get_last_day_of_next_month",
]


def get_last_day_of_month(input_date: date) -> date:
    """Given a date object, computes the last date of the month.

    Args:
        input_date: The base date to offset.

    Returns:
        The computed offset date.
    """
    year = input_date.year
    month = input_date.month

    last_day = calendar.monthrange(year, month)[1]
    return input_date.replace(day=last_day)


def get_last_day_of_next_month(input_date: date) -> date:
    """Given a date object, computes the last date of the next calendar month.

    Args:
        input_date: The base date to offset.

    Returns:
        The computed offset date.
    """
    year = input_date.year
    month = input_date.month

    if month == 12:
        next_month_year = year + 1
        next_month = 1
    else:
        next_month_year = year
        next_month = month + 1

    last_day_next_month = calendar.monthrange(next_month_year, next_month)[1]
    return date(next_month_year, next_month, last_day_next_month)
