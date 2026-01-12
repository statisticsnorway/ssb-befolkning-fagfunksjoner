import pytest

from ssb_befolkning_fagfunksjoner import EventParams


@pytest.mark.parametrize(
    "year, period_type, period_number, expected_label",
    [
        # Year
        (2024, "year", None, "p2024"),
        # Halfyear
        (2024, "halfyear", 1, "p2024-H1"),
        (2024, "halfyear", 2, "p2024-H2"),
        # Quarter
        (2024, "quarter", 1, "p2024-Q1"),
        (2024, "quarter", 4, "p2024-Q4"),
        # Month (check zero-padding)
        (2024, "month", 1, "p2024-01"),
        (2024, "month", 10, "p2024-10"),
        # Week (check zero-padding)
        (2024, "week", 2, "p2024-W02"),
        (2024, "week", 12, "p2024-W12"),
    ],
)
def test_period_label_formats_correctly(
    year: int,
    period_type: str,
    period_number: int | None,
    expected_label: str,
) -> None:
    """Ensure that period_label returns the correct formatted string
    for different period types and numbers.
    """

    # Arrange
    params = EventParams(
        year=year,
        period_type=period_type,
        period_number=period_number,
        specify_wait_period=False,
    )

    # Act
    label = params.period_label

    # Assert
    assert label == expected_label


@pytest.mark.parametrize(
    "wait_months, wait_days, expected_label",
    [
        # Default wait period (1m0d)
        (1, 0, "1m0d"),
        # Pure day-based wait
        (0, 7, "0m7d"),
        # Only months
        (2, 0, "2m0d"),
        # Mixed months and days
        (3, 5, "3m5d"),
    ],
)
def test_etterslep_label_formats_correctly(
    wait_months: int,
    wait_days: int,
    expected_label: str,
) -> None:
    """Ensure that the etterslep_label string is formatted correctly
    for different combinations of wait_months and wait_days.
    """
    
    # Arrange
    params = EventParams(
        year=2024,
        period_type="month",
        period_number=1,
        specify_wait_period=False,
    )
    # Override defaults for testing
    params.wait_months = wait_months
    params.wait_days = wait_days

    # Act
    label = params.etterslep_label

    # Assert
    assert label == expected_label
