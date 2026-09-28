import calendar
import datetime

__all__ = [
    "get_last_day_of_month",
    "get_last_day_of_next_month",
    "validate_reference_date",
]


def validate_reference_date(s: str) -> datetime.date:
    """Validate and return a date from a date string.

    Args:
        s: The date string in format YYYY-MM-DD or YYYYMMDD.
    
    Returns:
        date: The validated date object.

    Raises:
        ValueError: If the string is not a valid date.
    """
    if len(s) not in (8, 10):
        raise ValueError(f"Invalid reference-date '{s}'. Expected YYYY-MM-DD or YYYYMMDD.")
    try:
        return datetime.date.fromisoformat(s)
    except ValueError:
        try:
            return datetime.datetime.strptime(s, "%Y%m%d").date()
        except ValueError as e:
            raise ValueError(f"Invalid reference-date '{s}'. Expected YYYY-MM-DD or YYYYMMDD.") from e




def get_last_day_of_month(input_date: datetime.date) -> datetime.date:
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


def get_last_day_of_next_month(input_date: datetime.date) -> datetime.date:
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
    return datetime.date(next_month_year, next_month, last_day_next_month)
