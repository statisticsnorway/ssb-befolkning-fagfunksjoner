"""This script contains the "public" functions of the date_utils module.

Functions:
    - get_date_parameters()
    - get_period_labels()
    - get_last_day_of_next_month()
    - get_last_day_of_month()
"""

import calendar
from datetime import date
from typing import Any
from typing import TypedDict

from ._date_utils import get_etterslep_dates
from ._date_utils import get_period_dates
from ._inputs import get_user_inputs
from ._labels import get_period_label


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
    start_date, end_date, _ = get_period_dates(year, period_type, period_number)
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


def get_period_labels(
    date_params: dict[str, Any], include_etterslep: bool = True
) -> str | tuple[str, str]:
    """Returns a tuple of strings for period label and etterslep label for filename."""
    period_label = get_period_label(
        date_params["year"], date_params["period_type"], date_params["period_number"]
    )

    if include_etterslep:
        etterslep_label = f"{date_params['wait_months']}m{date_params['wait_days']}d"
        return period_label, etterslep_label

    return period_label


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
