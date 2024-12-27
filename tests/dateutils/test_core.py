import pytest

from datetime import date
from ssb_befolkning_fagfunksjoner.dateutils.core import (
    get_period_dates,
    get_etterslep_dates,
    get_period_label,
)


def test_get_period_dates():
    start, end, late_reg = get_period_dates(2024, "year")
    assert start == date(2024, 1, 1)
    assert end == date(2024, 12, 31)
    assert late_reg is True


@pytest.mark.parameterise("period_type, period_num, expected_end_day", [
    ("quarter", 1, date(2024, 3, 31)),
    ("quarter", 2, date(2024, 6, 30)),
    ("month", 3, date(2024, 3, 31)),
])
def test_get_period_dates_various(period_type, period_num, expected_end_day):
    _, end, late_reg = get_period_dates(2024, period_type, period_num)
    assert end == expected_end_day
    assert late_reg is True


def test_get_period_dates_errors():
    with pytest.raises(ValueError):
        get_period_dates(2024, "month")


def test_get_etterslep_dates():
    start_date = date(2024, 1, 1)
    end_date = date(2024, 1, 31)
    new_start, new_end = get_etterslep_dates(start_date, end_date, wait_months=1, wait_days=0)
    assert new_start == date(2024, 2, 1)
    assert new_end == date(2024, 2, 29)  # indirectly tests _add_wait_period() 


def test_get_period_label():
    assert get_period_label(2024, "year") == "p2024"
    assert get_period_label(2024, "halfyear", 1) == "p2024-H1"
    assert get_period_label(2024, "quarter", 1) == "p2024-Q1"
    assert get_period_label(2024, "month", 1) == "p2024-01"
    assert get_period_label(2024, "week", 1) == "p2024-W01"


def test_get_period_label_errors():
    with pytest.raises(ValueError):
        get_period_label(2024, "month")