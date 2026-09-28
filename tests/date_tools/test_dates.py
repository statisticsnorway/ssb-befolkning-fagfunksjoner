from datetime import date

import pytest

from ssb_befolkning_fagfunksjoner.date_tools.dates import get_last_day_of_month
from ssb_befolkning_fagfunksjoner.date_tools.dates import get_last_day_of_next_month
from ssb_befolkning_fagfunksjoner.date_tools.dates import validate_reference_date

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


# ---------------- validate_reference_date ----------------
cases_validate_reference_date = [
    ("2024-12-31", date(2024, 12, 31)),
    ("20241231", date(2024, 12, 31)),
    ("2024-02-29", date(2024, 2, 29)),
]


@pytest.mark.parametrize("input_str, expected", cases_validate_reference_date)
def test_validate_reference_date(input_str: str, expected: date) -> None:
    result = validate_reference_date(input_str)
    assert result == expected


@pytest.mark.parametrize(
    "invalid_str",
    [
        "2024/12/31",
        "202412",
        "not-a-date",
        "2024-02-30",
        "20240230",
    ],
)
def test_validate_reference_date_invalid(invalid_str: str) -> None:
    with pytest.raises(ValueError, match="Invalid reference-date"):
        validate_reference_date(invalid_str)
