"""
core.py

This script defines the core logic for calculating date periods and labels.
It contains 3 main functions: 
    - get_period_dates
    - get_etterslep_dates
    - get_period_label

Usage:
    from core import get_period_dates, get_period_label
    start, end, include_late = get_period_dates(2024, "quarter", 2)
    label = get_period_label(2024, "quarter", 2)
"""


from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
import calendar


def get_period_dates(year: int, period_type: str, period_number: int|None = None) -> tuple[date, date, bool]:
    """
    Calculate the start and end dates of a given period.
    
    Parameters:
    - year (int): The reference year.
    - period_type (str): One of 'year', 'quarter', 'month', 'week', 'halfyear'.
    - period_number (int): The specific period number within the year.
      For 'year', it can be None since the entire year is the period.

    Returns:
    - (start_date: date, end_date: date, include_late_reg: bool)
    """
    if period_type == "year":
        return _get_year_dates(year)

    if period_number is None:
        raise ValueError(f"period_number cannot be None for '{period_type}'.")

    if period_type == "halfyear":
        return _get_halfyear_dates(year, period_number)
    elif period_type == "quarter":
        return _get_quarter_dates(year, period_number)
    elif period_type == "month":
        return _get_month_dates(year, period_number)
    elif period_type == "week":
        return _get_week_dates(year, period_number)

    raise ValueError(f"Unexpected period_type: {period_type}")



def get_etterslep_dates(start_date: date, end_date: date, wait_months: int, wait_days: int) -> tuple[date, date]:
    """
    Calculate the waitperiod dates given a start date and and end date, and wait times.

    Parameters:
    - start_date (date): start of base period
    - end_date (date): end of base period
    - wait_months (int): number of months to wait in data collection
    - wait_days (int): number of days to wait in data collection

    Returns:
    - (etterslep_start: date, etterslep_end: date)
    """
    if wait_months > 0:
        etterslep_start = start_date + relativedelta(months=wait_months)
        etterslep_end = _add_wait_period(date_dt=end_date, add_months=wait_months, add_days=wait_days)
    else:
        etterslep_start = start_date + timedelta(days=wait_days)
        etterslep_end = end_date + timedelta(days=wait_days)

    return etterslep_start, etterslep_end


def get_period_label(year: int, period_type: str, period_number: int|None = None) -> str:
    """
    Generate a label string for the given period.
    
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


# ------------------------------------------------------------------------------------------
# Helper functions
# ------------------------------------------------------------------------------------------


def _get_year_dates(year: int) -> tuple[date, date, bool]:
    start_date = date(year, 1, 1)
    end_date = start_date + relativedelta(years=1) - relativedelta(days=1)
    include_late_reg = True
    return start_date, end_date, include_late_reg


def _get_halfyear_dates(year: int, halfyear: int) -> tuple[date, date, bool]:
    if halfyear not in (1, 2):
        raise ValueError("Halfyear must be 1 or 2.")
    start_month = 1 if halfyear == 1 else 7
    start_date = date(year, start_month, 1)
    end_date = start_date + relativedelta(months=6) - relativedelta(days=1)
    include_late_reg = True
    return start_date, end_date, include_late_reg


def _get_quarter_dates(year: int, quarter: int) -> tuple[date, date, bool]:
    if quarter is None or not (1 <= quarter <= 4):
        raise ValueError("Quarter must be between 1 and 4.")
    start_month = (quarter - 1) * 3 + 1
    start_date = date(year, start_month, 1)
    end_date = start_date + relativedelta(months=3) - relativedelta(days=1)
    include_late_reg = True
    return start_date, end_date, include_late_reg


def _get_month_dates(year: int, month: int) -> tuple[date, date, bool]:
    if month is None or not (1 <= month <= 12):
        raise ValueError("Month must be between 1 and 12.")
    start_date = date(year, month, 1)
    end_date = start_date + relativedelta(months=1) - relativedelta(days=1)
    include_late_reg = True
    return start_date, end_date, include_late_reg


def _get_week_dates(year: int, week: int) -> tuple[date, date, bool]:
    if week is None or not (1 <= week <= 53):
        raise ValueError("Week must be between 1 and 53.")
    start_date = date.fromisocalendar(year, week, 1)
    end_date = start_date + timedelta(days=6)
    include_late_reg = True
    return start_date, end_date, include_late_reg


def _add_wait_period(date_dt: date, add_months: int, add_days: int) -> date:
    """
    Adjusts the given date by adding months and moving to the end of the new month.
    """
    date_dt = date_dt + relativedelta(months=add_months)
    days_in_new_month = calendar.monthrange(date_dt.year, date_dt.month)[1]
    date_dt = date_dt.replace(day=days_in_new_month)
    date_dt += timedelta(days=add_days)
    return date_dt