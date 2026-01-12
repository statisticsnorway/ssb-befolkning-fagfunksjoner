from datetime import date

import pytest

from ssb_befolkning_fagfunksjoner import EventParams


@pytest.mark.parametrize(
    "year, period_type, period_number, expected_start, expected_end",
    [
        # Year
        (2024, "year", None, date(2024, 1, 1), date(2024, 12, 31)),
        # Halfyear
        (2024, "halfyear", 1, date(2024, 1, 1), date(2024, 6, 30)),
        (2024, "halfyear", 2, date(2024, 7, 1), date(2024, 12, 31)),
        # Quarter
        (2024, "quarter", 1, date(2024, 1, 1), date(2024, 3, 31)),
        (2024, "quarter", 4, date(2024, 10, 1), date(2024, 12, 31)),
        # Month (incl. leap-year February)
        (2024, "month", 2, date(2024, 2, 1), date(2024, 2, 29)),
        (2024, "month", 4, date(2024, 4, 1), date(2024, 4, 30)),
        # Week (ISO week)
        (2024, "week", 10, date(2024, 3, 4), date(2024, 3, 10)),
    ],
)
def test_window_returns_correct_date_range(
    year: int,
    period_type: str,
    period_number: int | None,
    expected_start: date,
    expected_end: date,
) -> None:
    """Ensure that window returns the correct start and end dates for different period types and numbers.
    """
    # Arrange
    params = EventParams(
        year=year,
        period_type=period_type,
        period_number=period_number,
        specify_wait_period=False,
    )

    # Act
    start_date, end_date = params.window

    # Assert
    assert start_date == expected_start
    assert end_date == expected_end


@pytest.mark.parametrize(
    "year, period_type, period_number, wait_months, wait_days, expected_start, expected_end",
    [
        # Default wait period applied to a month (March → April)
        (
            2024,
            "month",
            3,
            1,
            0,
            date(2024, 4, 1),  # start + 1 month
            date(2024, 4, 30),  # end + 1 month, snapped to end of April
        ),
        # Pure day-based wait for a week (7 days forward)
        (
            2024,
            "week",
            10,
            0,
            7,
            date(2024, 3, 11),  # 7 days after Mar 4
            date(2024, 3, 17),  # 7 days after Mar 10
        ),
        # Month rollover: December 2024 → January 2025
        (
            2024,
            "quarter",
            4,
            1,
            0,
            date(2024, 11, 1),
            date(2025, 1, 31),
        ),
        # Leap year end-boundary logic: January 2024 end → February 2024 (29 days)
        (
            2024,
            "month",
            1,
            1,
            0,
            date(2024, 2, 1),
            date(2024, 2, 29),  # leap year
        ),
        # Non-leap year: January 2023 → February 2023 (28 days)
        (
            2023,
            "month",
            1,
            1,
            0,
            date(2023, 2, 1),
            date(2023, 2, 28),
        ),
    ],
)
def test_etterslep_window(
    year: int,
    period_type: str,
    period_number: int | None,
    wait_months: int,
    wait_days: int,
    expected_start: date,
    expected_end: date,
) -> None:
    """Ensure that etterslep_window returns correct dates for various wait-period configurations and calendar boundary cases.
    """
    # Arrange
    params = EventParams(
        year=year,
        period_type=period_type,
        period_number=period_number,
        specify_wait_period=False,
    )
    # Override wait values
    params.wait_months = wait_months
    params.wait_days = wait_days

    # Act
    start, end = params.etterslep_window

    # Assert
    assert start == expected_start
    assert end == expected_end
