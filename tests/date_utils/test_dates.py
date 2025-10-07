import datetime as dt
import pytest

from ssb_befolkning_fagfunksjoner.date_utils.dates import (
    get_last_day_of_month,
    get_last_day_of_next_month,
)

# ---------------- get_last_day_of_month ----------------
cases_last_day_of_month = [
    # (input_date, expected_output)
    (dt.date(2024, 1, 15), dt.date(2024, 1, 31)),   # Regular month
    (dt.date(2024, 2, 1), dt.date(2024, 2, 29)),    # Leap year February
    (dt.date(2023, 2, 10), dt.date(2023, 2, 28)),   # Non-leap year February
    (dt.date(2024, 12, 25), dt.date(2024, 12, 31)), # December
]

@pytest.mark.parametrize("input_date, expected", cases_last_day_of_month)
def test_get_last_day_of_month(input_date, expected):
    result = get_last_day_of_month(input_date)
    assert result == expected


# ---------------- get_last_day_of_next_month ----------------
cases_last_day_of_next_month = [
    (dt.date(2024, 1, 15), dt.date(2024, 2, 29)),   # Leap year
    (dt.date(2023, 1, 31), dt.date(2023, 2, 28)),   # Jan → Feb (non-leap)
    (dt.date(2024, 11, 30), dt.date(2024, 12, 31)), # Nov → Dec
    (dt.date(2024, 12, 1), dt.date(2025, 1, 31)),   # Year boundary
]

@pytest.mark.parametrize("input_date, expected", cases_last_day_of_next_month)
def test_get_last_day_of_next_month(input_date, expected):
    result = get_last_day_of_next_month(input_date)
    assert result == expected
