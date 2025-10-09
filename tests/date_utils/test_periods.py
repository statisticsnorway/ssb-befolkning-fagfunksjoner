from typing import Any

import pytest

from ssb_befolkning_fagfunksjoner.date_utils.periods import (
    get_standardised_period_label,
)

valid_cases: list[tuple[list[Any], str]] = [
    ([2025, "halfyear", 2], "p2025-H2"),
    ([2024, "quarter", 3], "p2024-Q3"),
    ([2024, "month", 3], "p2024-03"),
    ([2024, "week", 7], "p2024W07"),
    ([2025, "year", None], "p2025"),
]


@pytest.mark.parametrize("inputs, expected", valid_cases)
def test_get_standardised_period_label_valid(inputs: list, expected: str) -> None:
    assert get_standardised_period_label(*inputs) == expected


invalid_cases: list[tuple[list[Any], str]] = [
    # invalid period type
    ([2025, "years", None], r"Invalid period type: 'years'\."),
    # missing period_number where required
    ([2025, "quarter", None], r"'period_number' must be provided for 'quarter'\."),
    # out-of-range checks
    ([2025, "halfyear", 0], r"halfyear must be 1 or 2\."),
    ([2025, "halfyear", 3], r"halfyear must be 1 or 2\."),
    ([2024, "quarter", 5], r"quarter must be between 1 and 4\."),
    ([2024, "month", 13], r"month must be between 1 and 12\."),
    ([2024, "week", 0], r"week must be between 1 and 53\."),
    ([2024, "week", 54], r"week must be between 1 and 53\."),
]


@pytest.mark.parametrize("inputs, message_regex", invalid_cases)
def test_get_standardised_period_label_invalid(
    inputs: list[Any], message_regex: str
) -> None:
    with pytest.raises(ValueError, match=message_regex):
        get_standardised_period_label(*inputs)
