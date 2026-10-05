from datetime import date

import pytest

from ssb_befolkning_fagfunksjoner.parameters.validators import choice
from ssb_befolkning_fagfunksjoner.parameters.validators import int_in_range
from ssb_befolkning_fagfunksjoner.parameters.validators import validate_bool
from ssb_befolkning_fagfunksjoner.parameters.validators import validate_reference_date

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
        "",
    ],
)
def test_validate_reference_date_invalid(invalid_str: str) -> None:
    with pytest.raises(ValueError, match="Invalid reference-date"):
        validate_reference_date(invalid_str)


# ---------------- validate_bool ----------------
cases_validate_bool_true = ["true", "TRUE", "yes", "Yes", "y", "1", " true "]
cases_validate_bool_false = ["false", "FALSE", "no", "No", "n", "0", " false "]


@pytest.mark.parametrize("input_str", cases_validate_bool_true)
def test_validate_bool_true(input_str: str) -> None:
    assert validate_bool(input_str) is True


@pytest.mark.parametrize("input_str", cases_validate_bool_false)
def test_validate_bool_false(input_str: str) -> None:
    assert validate_bool(input_str) is False


@pytest.mark.parametrize("invalid_str", ["", "maybe", "2", "truthy"])
def test_validate_bool_invalid(invalid_str: str) -> None:
    with pytest.raises(ValueError, match="Enter true/false"):
        validate_bool(invalid_str)


# ---------------- int_in_range ----------------
cases_int_in_range = [
    (1, 10, "1", 1),  # Lower bound
    (1, 10, "10", 10),  # Upper bound
    (1, 10, "5", 5),  # Mid-range
    (1, 10, " 7 ", 7),  # Surrounding whitespace is stripped
    (0, None, "0", 0),  # No upper bound
    (0, None, "123", 123),  # No upper bound
]


@pytest.mark.parametrize("low, high, input_str, expected", cases_int_in_range)
def test_int_in_range(
    low: int, high: int | None, input_str: str, expected: int
) -> None:
    assert int_in_range(low, high)(input_str) == expected


@pytest.mark.parametrize(
    "low, high, invalid_str",
    [
        (1, 10, "0"),  # Below lower bound
        (1, 10, "11"),  # Above upper bound
        (0, None, "-1"),  # Below lower bound, no upper bound
    ],
)
def test_int_in_range_out_of_bounds(
    low: int, high: int | None, invalid_str: str
) -> None:
    with pytest.raises(ValueError, match="Enter a value"):
        int_in_range(low, high)(invalid_str)


@pytest.mark.parametrize(
    "low, high, invalid_str",
    [
        (1, 10, "abc"),  # Not a number
        (1, 10, ""),  # Empty input
        (1, 10, "1.5"),  # Not an integer
    ],
)
def test_int_in_range_not_an_integer(
    low: int, high: int | None, invalid_str: str
) -> None:
    with pytest.raises(ValueError, match="not a valid integer"):
        int_in_range(low, high)(invalid_str)


def test_int_in_range_error_message_reports_bounds() -> None:
    with pytest.raises(ValueError, match="between 1 and 10"):
        int_in_range(1, 10)("99")


def test_int_in_range_error_message_without_upper_bound() -> None:
    with pytest.raises(ValueError, match="of at least 5"):
        int_in_range(5)("1")


# ---------------- choice ----------------
PERIODS = ("year", "halfyear", "quarter", "month", "week")

cases_choice_exact = [
    ("year", "year"),
    ("halfyear", "halfyear"),
    ("quarter", "quarter"),
    ("month", "month"),
    ("week", "week"),
]

cases_choice_unambiguous_prefix = [
    ("y", "year"),
    ("h", "halfyear"),
    ("q", "quarter"),
    ("m", "month"),
    ("w", "week"),
    ("qu", "quarter"),
]


@pytest.mark.parametrize("input_str, expected", cases_choice_exact)
def test_choice_exact_match(input_str: str, expected: str) -> None:
    assert choice(PERIODS)(input_str) == expected


@pytest.mark.parametrize("input_str, expected", cases_choice_unambiguous_prefix)
def test_choice_unambiguous_prefix(input_str: str, expected: str) -> None:
    assert choice(PERIODS)(input_str) == expected


@pytest.mark.parametrize(
    "input_str, expected",
    [
        ("YEAR", "year"),  # Case insensitive
        ("Year", "year"),
        ("  year  ", "year"),  # Surrounding whitespace is stripped
    ],
)
def test_choice_normalises_input(input_str: str, expected: str) -> None:
    assert choice(PERIODS)(input_str) == expected


@pytest.mark.parametrize("invalid_str", ["", "   ", "z", "not-a-period"])
def test_choice_invalid(invalid_str: str) -> None:
    with pytest.raises(ValueError, match="Choose one of:"):
        choice(PERIODS)(invalid_str)


def test_choice_rejects_ambiguous_prefix() -> None:
    # "ap" matches both options, so it cannot be resolved.
    with pytest.raises(ValueError, match="Choose one of: apple/apricot"):
        choice(("apple", "apricot"))("ap")


def test_choice_error_message_lists_options() -> None:
    with pytest.raises(
        ValueError, match=r"Choose one of: year/halfyear/quarter/month/week\."
    ):
        choice(PERIODS)("nope")
