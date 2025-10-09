import builtins
from datetime import date
from typing import Any

import pytest
from pytest_mock import MockerFixture

from ssb_befolkning_fagfunksjoner.date_utils.date_parameters import get_date_parameters

cases: list[tuple[list[str], dict[str, Any]]] = [
    (
        ["2025", "year", "", ""],
        {
            "year": 2025,
            "period_type": "year",
            "period_number": None,
            "start_date": date(2025, 1, 1),
            "end_date": date(2025, 12, 31),
            "etterslep_start": date(2025, 1, 8),
            "etterslep_end": date(2026, 1, 7),
            "wait_days": 7,
            "wait_months": 0,
        },
    ),
    (
        ["2024", "quarter", "2", "1", "0"],
        {
            "year": 2024,
            "period_type": "quarter",
            "period_number": 2,
            "start_date": date(2024, 4, 1),
            "end_date": date(2024, 6, 30),
            "etterslep_start": date(2024, 5, 1),
            "etterslep_end": date(2024, 7, 31),
            "wait_days": 0,
            "wait_months": 1,
        },
    ),
    (
        ["1991", "week", "17", "0", "0"],
        {
            "year": 1991,
            "period_type": "week",
            "period_number": 17,
            "start_date": date(1991, 4, 22),
            "end_date": date(1991, 4, 28),
            "etterslep_start": date(1991, 4, 22),
            "etterslep_end": date(1991, 4, 28),
            "wait_days": 0,
            "wait_months": 0,
        },
    ),
]


@pytest.mark.parametrize("inputs, expected", cases)
def test_get_date_parameters(
    mocker: MockerFixture, inputs: list[str], expected: dict[str, Any]
) -> None:
    mocker.patch.object(builtins, "input", side_effect=inputs)
    result = get_date_parameters()

    assert result == expected
