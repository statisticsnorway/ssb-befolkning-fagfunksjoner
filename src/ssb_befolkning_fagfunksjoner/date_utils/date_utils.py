"""This script contains the "public" functions of the date_utils module.

Functions:
    - get_date_parameters()
    - get_period_label()
    - get_period_dates()
    - get_last_day_of_next_month()
    - get_last_day_of_month()
"""

__all__ = [
    "get_date_parameters",
    "get_last_day_of_month",
    "get_last_day_of_next_month",
    "get_period_dates",
    "get_period_label",
]

import calendar
from datetime import date
from typing import TypedDict

from ._date_utils import get_etterslep_dates
from ._date_utils import get_period_dates
from ._inputs import get_user_inputs


class DateParameters(TypedDict):
    """Typed dictionary containing date parameters for a given event period.

    Attributes:
    - year (int): The reference year.
    - period_type (str): The period type.
    - period_number (int | None): The specific period number.
    - start_date (date): The start date of the period.
    - end_date (date): The end date of the period.
    - etterslep_start (date): The start date of the etterslep period.
    - etterslep_end (date): The end date of the etterslep period.
    - wait_days (int): Number of days to wait before considering data complete.
    - wait_months (int): Number of months to wait before considering data complete.
    """

    year: int
    period_type: str
    period_number: int | None
    start_date: date
    end_date: date
    etterslep_start: date
    etterslep_end: date
    wait_days: int
    wait_months: int


def get_date_parameters() -> DateParameters:
    """Return a dictionary of query parameters for the specified event."""
    year, period_type, period_number, wait_months, wait_days = get_user_inputs(
        specify_wait_period=True
    )
    start_date, end_date = get_period_dates(year, period_type, period_number)
    etterslep_start, etterslep_end = get_etterslep_dates(
        start_date, end_date, wait_months, wait_days
    )

    return {
        "year": year,
        "period_type": period_type,
        "period_number": period_number,
        "start_date": start_date,
        "end_date": end_date,
        "etterslep_start": etterslep_start,
        "etterslep_end": etterslep_end,
        "wait_days": wait_days,
        "wait_months": wait_months,
    }


def get_period_label(
    year: int, period_type: str, period_number: int | None = None
) -> str:
    """Generate a label string for the given period.

    Parameters:
    - year (int): the reference year
    - period_type (str): One of 'year', 'halfyear', 'quarter', 'month', 'week'
    - period_number: the sub-period number, if applicable.

    Returns:
    - period_label (str): a formatted string label

    Examples:
      - year: p2024
      - halfyear: p2024H1
      - quarter: p2024-Q2
      - month: p2024-05
      - week: p2024W12
    """
    if period_type == "year":
        return f"p{year}"
    elif period_type == "halfyear":
        if period_number is None:
            raise ValueError("period_number must be provided for halfyear.")
        return f"p{year}H{period_number}"
    elif period_type == "quarter":
        if period_number is None:
            raise ValueError("period_number must be provided for quarter.")
        return f"p{year}-Q{period_number}"
    elif period_type == "month":
        if period_number is None:
            raise ValueError("period_number must be provided for month.")
        return f"p{year}-{str(period_number).zfill(2)}"
    elif period_type == "week":
        if period_number is None:
            raise ValueError("period_number must be provided for week.")
        return f"p{year}W{str(period_number).zfill(2)}"
    else:
        raise ValueError(f"Invalid period type: {period_type}")


def get_last_day_of_month(input_date: date) -> date:
    """Given a date object, return a new date object representing the last day of that month."""
    year = input_date.year
    month = input_date.month

    last_day = calendar.monthrange(year, month)[1]
    return input_date.replace(day=last_day)


def get_last_day_of_next_month(input_date: date) -> date:
    """Given a date object, return a new date object representing the last day of the following month."""
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
