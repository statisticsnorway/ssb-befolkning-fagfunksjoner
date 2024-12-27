import calendar
from datetime import date


def get_next_period(
    year: int, period_type: str, period_number: int|None = None
) -> tuple[int, str, int|None]:
    """
    Given a period, defined by year, period_type, and period_number,
    returns the next consecutive period.
    """
    if period_type == "year":
        return (year + 1, "year", None)
    
    if period_number is None:
        raise ValueError(f"period_number cannot be None for '{period_type}'.")
    
    if period_type == "halfyear":
        if period_number == 2:
            return (year + 1, "halfyear", 1)
        return (year, "halfyear", period_number + 1)
    elif period_type == "quarter":
        if period_number == 4:
            return (year + 1, "quarter", 1)
        return (year, "quarter", period_number + 1)
    elif period_type == "month":
        if period_number == 12:
            return (year + 1, "month", 1)
        return (year, "month", period_number + 1)
    elif period_type == "week":
        raise ValueError("Next week is ambiguous at end of year.")

    raise ValueError(f"Unexpected period_type: {period_type}")


def get_last_period(
    year: int, period_type: str, period_number: int|None = None
) -> tuple[int, str, int|None]:
    """
    Given a period defined by year, period_type, and period_number,
    returns the previous consecutive period.
    """
    if period_type == "year":
        return (year - 1, "year", None)

    if period_number is None:
        raise ValueError(f"period_number cannot be None for '{period_type}'.")

    if period_type == "halfyear":
        if period_number == 1:
            return (year - 1, "halfyear", 2)
        return (year, "halfyear", period_number - 1)
    elif period_type == "quarter":
        if period_number == 1:
            return (year - 1, "quarter", 4)
        return (year, "quarter", period_number - 1)
    elif period_type == "month":
        if period_number == 1:
            return (year - 1, "month", 12)
        return (year, "month", period_number - 1)
    elif period_type == "week":
        raise ValueError("Last week is ambiguous at start of year.")

    raise ValueError(f"Unexpected period_type: {period_type}")


def get_last_day_of_month(input_date: date) -> date:
    """
    Given a date object, return a new date object representing
    the last day of that month.
    """
    year = input_date.year
    month = input_date.month

    last_day = calendar.monthrange(year, month)[1]
    return input_date.replace(day=last_day)


def get_last_day_of_next_month(input_date: date) -> date:
    """
    Given a date object, return a new date object representing
    the last day of the following month.
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