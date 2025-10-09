from datetime import date

import pytest

from ssb_befolkning_fagfunksjoner.date_utils.dates import get_last_day_of_month
from ssb_befolkning_fagfunksjoner.date_utils.dates import get_last_day_of_next_month

# ---------------- get_last_day_of_month ----------------
cases_last_day_of_month = [
    # (input_date, expected_output)
    (date(2024, 1, 15), date(2024, 1, 31)),  # Regular month
    (date(2024, 2, 1), date(2024, 2, 29)),  # Leap year February
    (date(2023, 2, 10), date(2023, 2, 28)),  # Non-leap year February
    (date(2024, 12, 25), date(2024, 12, 31)),  # December
]


@pytest.mark.parametrize("input_date, expected", cases_last_day_of_month)
def test_get_last_day_of_month(input_date: date, expected: date) -> None:
    result = get_last_day_of_month(input_date)
    assert result == expected


# ---------------- get_last_day_of_next_month ----------------
cases_last_day_of_next_month = [
    (date(2024, 1, 15), date(2024, 2, 29)),  # Leap year
    (date(2023, 1, 31), date(2023, 2, 28)),  # Jan → Feb (non-leap)
    (date(2024, 11, 30), date(2024, 12, 31)),  # Nov → Dec
    (date(2024, 12, 1), date(2025, 1, 31)),  # Year boundary
]


@pytest.mark.parametrize("input_date, expected", cases_last_day_of_next_month)
def test_get_last_day_of_next_month(input_date: date, expected: date) -> None:
    result = get_last_day_of_next_month(input_date)
    assert result == expected
