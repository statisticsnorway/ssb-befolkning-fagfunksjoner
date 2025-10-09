from datetime import date
from typing import TypedDict

from .dates import get_etterslep_dates
from .dates import get_period_dates

VALID_PERIOD_TYPES: set[str] = {"year", "halfyear", "quarter", "month", "week"}

__all__ = ["get_date_parameters"]


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
    year, period_type, period_number, wait_months, wait_days = _get_user_inputs(
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


def _prompt_for_int(prompt_msg: str, valid_range: tuple[int, int] | None = None) -> int:
    """Prompt user for an integer. Re-prompt if invalid or out of range."""
    while True:
        val_str = input(prompt_msg).strip()
        if not val_str.isdigit():
            print("Please enter a valid integer.")
            continue

        val = int(val_str)
        if valid_range and not (valid_range[0] <= val <= valid_range[1]):
            print(
                f"Please enter a value between {valid_range[0]} and {valid_range[1]}."
            )
            continue

        return val


def _get_user_inputs(
    specify_wait_period: bool = False,
) -> tuple[int, str, int | None, int, int]:
    """Prompt for input and return (year, period_type, period_number, wait_months, wait_days).

    If specify_wait_period is False, the function won't prompt for wait months/days
    and will return default values (0, 7).
    """
    year = _prompt_for_int("Year: ")

    while True:
        period_type = input(
            "Enter period type (year/halfyear/quarter/month/week): "
        ).strip()
        if period_type in VALID_PERIOD_TYPES:
            break
        else:
            print(
                "Invalid period type. Choose from year, halfyear, quarter, month, week."
            )

    if period_type == "year":
        period_number = None
    elif period_type == "halfyear":
        period_number = _prompt_for_int("Enter halfyear (1-2): ", (1, 2))
    elif period_type == "quarter":
        period_number = _prompt_for_int("Enter quarter (1-4): ", (1, 4))
    elif period_type == "month":
        period_number = _prompt_for_int("Enter month (1-12): ", (1, 12))
    elif period_type == "week":
        period_number = _prompt_for_int("Enter week (1-53): ", (1, 53))

    if specify_wait_period:
        wait_months_input = input("Enter wait months (default 0): ").strip()
        wait_months = int(wait_months_input) if wait_months_input.isdigit() else 0

        wait_days_input = input("Enter wait days (default 7): ").strip()
        wait_days = int(wait_days_input) if wait_days_input.isdigit() else 7
    else:
        wait_months = 0
        wait_days = 7

    return year, period_type, period_number, wait_months, wait_days
