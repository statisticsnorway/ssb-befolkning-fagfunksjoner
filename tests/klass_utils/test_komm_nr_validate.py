from contextlib import nullcontext as does_not_raise
from typing import Any

import pandas as pd
import pytest
from pytest_mock import MockerFixture
from ssb_befolkning_fagfunksjoner.klass_utils.komm_nr import validate_komm_nr

# ------------------------------------------------------------------------
# Common fixtures (used by multiple tests)
# ------------------------------------------------------------------------


@pytest.fixture
def mock_valid_codes() -> dict[str, str]:
    """Minimal valid KLASS dict that validate_kommnr expects from _load_kommnr().

    Keys are codes; values are descriptions.
    """
    return {
        "0301": "Oslo",
        "5501": "Tromsø",
        "4601": "Bergen",
        "1103": "Stavanger",
        "3301": "Drammen",
        "1508": "Ålesund",
        "1580": "Molde",
        "0000": "Sperret adresse",
    }


# ------------------------------------------------------------------------
# Test 1: check validity
# ------------------------------------------------------------------------
cases = [
    (pd.Series(["0301", "5501", "4601", "1103", "3301"]), does_not_raise()),
    (
        pd.Series(["0301", "5501", "4601", "1103", "9998"]),
        pytest.raises(
            ValueError, match=r"Invalid municipality codes found: \['9998'\]"
        ),
    ),
    (
        pd.Series(["0301", None]),
        pytest.raises(ValueError, match=r"Invalid municipality codes found: \[None\]"),
    ),
]


@pytest.mark.parametrize("codes, expect_error", cases)
def test_validate_kommnr_all_valid(
    mocker: MockerFixture,
    mock_valid_codes: dict[str, str],
    codes: pd.Series,
    expect_error: Any,
) -> None:
    mocker.patch(
        "ssb_befolkning_fagfunksjoner.kommnr.validate._load_kommnr",
        return_value=mock_valid_codes,
    )

    with expect_error:
        validate_komm_nr(codes, year=2024)


# ------------------------------------------------------------------------
# Test 2: verify _load_kommnr is invoked with the expected year argument
# ------------------------------------------------------------------------


def test_validate_kommnr_calls_loader_with_year(
    mocker: MockerFixture, mock_valid_codes: dict[str, str]
) -> None:
    """validate_kommnr passes a 'year' argument through to _load_kommnr.

    This test asserts the call value. If you change how the year is passed,
    update the expectation accordingly.
    """
    s = pd.Series(["0301"])
    mock_load_kommnr = mocker.patch(
        "ssb_befolkning_fagfunksjoner.kommnr.validate._load_kommnr",
        return_value=mock_valid_codes,
    )

    validate_komm_nr(s, year=2024)

    mock_load_kommnr.assert_called_once_with(
        "2024-01-02"
    )  # matches current implementation
