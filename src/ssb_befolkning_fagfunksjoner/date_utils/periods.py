__all__ = ["get_standardised_period_label"]


def get_standardised_period_label(
    year: int, period_type: str, period_number: int | None = None
) -> str:
    """Generate a label string formatted as Dapla standard for the given period.

    Parameters:
    - year (int): the reference year
    - period_type (str): One of 'year', 'halfyear', 'quarter', 'month', 'week'
    - period_number: the sub-period number, if applicable.

    Returns:
    - period_label (str): a formatted string label

    Examples:
      - year: p2024
      - halfyear: p2024-H1
      - quarter: p2024-Q2
      - month: p2024-05
      - week: p2024W12
    """
    VALID_PERIODS = {"year", "halfyear", "quarter", "month", "week"}
    
    if period_type not in VALID_PERIODS:
        raise ValueError(f"Invalid period type: '{period_type}'.")

    if period_type == "year":
        return f"p{year}"

    if period_number is None:
        raise ValueError(f"'period_number' must be provided for '{period_type}'.")

    if period_type == "halfyear":
        if not 1 <= period_number <= 2:
            raise ValueError("halfyear must be 1 or 2.")
        return f"p{year}-H{period_number}"
    
    elif period_type == "quarter":
        if not 1 <= period_number <= 4:
            raise ValueError("quarter must be between 1 and 4.")
        return f"p{year}-Q{period_number}"

    elif period_type == "month":
        if not 1 <= period_number <= 12:
            raise ValueError("month must be between 1 and 12.")
        return f"p{year}-{str(period_number).zfill(2)}"

    elif period_type == "week":
        if not 1 <= period_number <= 53:
            raise ValueError("week must be between 1 and 53.")
        return f"p{year}W{str(period_number).zfill(2)}"

    raise ValueError(f"Unhandled period type: {period_type}")
