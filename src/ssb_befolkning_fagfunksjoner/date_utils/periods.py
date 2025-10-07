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
    if period_type == "year":
        return f"p{year}"
    elif period_type == "halfyear":
        if period_number is None:
            raise ValueError("period_number must be provided for halfyear.")
        return f"p{year}-H{period_number}"
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
