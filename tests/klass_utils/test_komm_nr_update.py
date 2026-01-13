import pandas as pd
import pytest
from pytest_mock import MockerFixture

from ssb_befolkning_fagfunksjoner.klass_utils.komm_nr import update_komm_nr

# ------------------------------------------------------------------------
# Common fixtures
# ------------------------------------------------------------------------


@pytest.fixture
def komm_nr_changes() -> pd.DataFrame:
    # Example mappings: 5401 -> 5501, 3005 -> 3301
    return pd.DataFrame(
        {
            "old_code": ["5401", "3005"],
            "new_code": ["5501", "3301"],
        }
    )


@pytest.fixture
def komm_nr_splits() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "old_code": ["1507", "1507"],
            "new_code": ["1508", "1580"],
        }
    )


@pytest.fixture
def empty_splits() -> pd.DataFrame:
    return pd.DataFrame({"old_code": [], "new_code": []})


# ------------------------------------------------------------------------
# Test 1: update + validate - parameterised toggle for validate
# ------------------------------------------------------------------------
cases = [
    (
        pd.Series(["0301", "5401", "4601", "1103", "3005"]),
        pd.Series(["0301", "5501", "4601", "1103", "3301"]),
        True,
        True,
    ),
    (
        pd.Series(["0301", "5401", "4601", "1103", "3005"]),
        pd.Series(["0301", "5501", "4601", "1103", "3301"]),
        False,
        False,
    ),
]


@pytest.mark.parametrize("original, expected, validate, expect_called", cases)
def test_update_kommnr_and_validate(
    mocker: MockerFixture,
    komm_nr_changes: pd.DataFrame,
    empty_splits: pd.DataFrame,
    original: pd.Series,
    expected: pd.Series,
    validate: bool,
    expect_called: bool,
) -> None:
    """Updates are applied; validation is invoked only when requested."""
    # Patch functions called in update_komm_nr()
    mocker.patch(
        "ssb_befolkning_fagfunksjoner.klass_utils.komm_nr.get_komm_nr_changes",
        return_value=(komm_nr_changes, empty_splits),
    )

    mock_validate = mocker.patch(
        "ssb_befolkning_fagfunksjoner.klass_utils.komm_nr.validate_komm_nr",
    )

    result = update_komm_nr(original_codes=original, year=2024, validate=validate)
    pd.testing.assert_series_equal(result, expected, check_names=False)
    if expect_called:
        mock_validate.assert_called_once_with(result, 2024)
    else:
        mock_validate.assert_not_called()


# ------------------------------------------------------------------------
# Test 2: splits - unchanged split codes + warning
# ------------------------------------------------------------------------


def test_update_without_validation(
    mocker: MockerFixture,
    komm_nr_changes: pd.DataFrame,
    komm_nr_splits: pd.DataFrame,
) -> None:
    """When there are split codes, codes remain as-is and a warning is raised."""
    original = pd.Series(["0301", "5401", "4601", "1103", "3005", "1507"])
    expected = pd.Series(["0301", "5501", "4601", "1103", "3301", "1507"])

    # Patch functions called in update_kommnr()
    mocker.patch(
        "ssb_befolkning_fagfunksjoner.klass_utils.komm_nr.get_komm_nr_changes",
        return_value=(komm_nr_changes, komm_nr_splits),
    )

    mock_validate = mocker.patch(
        "ssb_befolkning_fagfunksjoner.klass_utils.komm_nr.validate_komm_nr",
    )

    with pytest.warns(UserWarning, match=r"splits"):
        result = update_komm_nr(original, 2024, validate=False)

    pd.testing.assert_series_equal(result, expected, check_names=False)
    mock_validate.assert_not_called()


# ------------------------------------------------------------------------
# Test 3: recursive mapping
# ------------------------------------------------------------------------


@pytest.fixture
def recursive_changes() -> pd.DataFrame:
    return pd.DataFrame({"old_code": ["1111", "2222"], "new_code": ["2222", "3333"]})


def test_recursive_mapping(
    mocker: MockerFixture,
    recursive_changes: pd.DataFrame,
    empty_splits: pd.DataFrame,
) -> None:
    """Recursive updates are applied (e.g., 1111 -> 2222 -> 3333)."""
    original = pd.Series(["1111", "0301"])
    expected = pd.Series(["3333", "0301"])

    mocker.patch(
        "ssb_befolkning_fagfunksjoner.klass_utils.komm_nr.get_komm_nr_changes",
        return_value=(recursive_changes, empty_splits),
    )
    mocker.patch("ssb_befolkning_fagfunksjoner.klass_utils.komm_nr.validate_komm_nr")

    result = update_komm_nr(original, 2024, validate=True)
    pd.testing.assert_series_equal(result, expected, check_names=False)


# ------------------------------------------------------------------------
# Test 4: NA handling - missing filled with "0000" to match Klass
# ------------------------------------------------------------------------


@pytest.fixture
def empty_changes() -> pd.DataFrame:
    return pd.DataFrame({"old_code": [], "new_code": []})


def test_na_filled_with_0000(
    mocker: MockerFixture,
    empty_changes: pd.DataFrame,
    empty_splits: pd.DataFrame,
) -> None:
    """Missing codes are filled with '0000' prior to validation."""
    original = pd.Series(["0301", None])
    expected = pd.Series(["0301", "0000"])

    mocker.patch(
        "ssb_befolkning_fagfunksjoner.klass_utils.komm_nr.get_komm_nr_changes",
        return_value=(empty_changes, empty_splits),
    )
    mocker.patch("ssb_befolkning_fagfunksjoner.klass_utils.komm_nr.validate_komm_nr")

    result = update_komm_nr(original, 2024, validate=True)
    pd.testing.assert_series_equal(result, expected, check_names=False)
