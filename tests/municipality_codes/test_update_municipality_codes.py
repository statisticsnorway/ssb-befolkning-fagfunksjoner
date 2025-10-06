import pandas as pd
import pytest
from pytest_mock import MockerFixture

from ssb_befolkning_fagfunksjoner.municipality_codes.update_codes import (
    update_municipality_codes,
)


@pytest.fixture
def kommnr_changes() -> pd.DataFrame:
    # Example mappings: 5401 -> 5501, 3005 -> 3301
    return pd.DataFrame(
        {
            "old_code": ["5401", "3005"],
            "new_code": ["5501", "3301"],
        }
    )


@pytest.fixture
def empty_splits() -> pd.DataFrame:
    return pd.DataFrame({"old_code": [], "new_code": []})


@pytest.fixture
def kommnr_splits() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "old_code": ["1507", "1507"],
            "new_code": ["1508", "1580"],
        }
    )


@pytest.fixture
def mock_valid_codes() -> set[str]:
    # The KLASS list you want to be valid at the validation date
    return {"0301", "5501", "4601", "1103", "3301", "1508", "1580", "0000"}


def test_update_and_validate(
    mocker: MockerFixture,
    kommnr_changes: pd.DataFrame,
    empty_splits: pd.DataFrame,
    mock_valid_codes: set[str],
) -> None:
    original = pd.Series(["0301", "5401", "4601", "1103", "3005"])
    expected = pd.Series(["0301", "5501", "4601", "1103", "3301"])

    mocker.patch(
        "ssb_befolkning_fagfunksjoner.municipality_codes.update_codes.load_kommnr_changes",
        return_value=(kommnr_changes, empty_splits),
    )

    mocker.patch(
        "ssb_befolkning_fagfunksjoner.municipality_codes.validation.load_kommnr",
        return_value={code: {} for code in mock_valid_codes},
    )

    mock_validate_municipality_codes = mocker.patch(
        "ssb_befolkning_fagfunksjoner.municipality_codes.update_codes.validate_municipality_codes",
    )

    result = update_municipality_codes(
        original_codes=original, year=2024, validate=True
    )

    pd.testing.assert_series_equal(result, expected, check_names=False)
    mock_validate_municipality_codes.assert_called_once_with(result, 2024)


def test_update_without_validation(
    mocker: MockerFixture, kommnr_changes: pd.DataFrame, kommnr_splits: pd.DataFrame
) -> None:
    original = pd.Series(["0301", "5401", "4601", "1103", "3005", "1507"])
    expected = pd.Series(["0301", "5501", "4601", "1103", "3301", "1507"])

    mocker.patch(
        "ssb_befolkning_fagfunksjoner.municipality_codes.update_codes.load_kommnr_changes",
        return_value=(kommnr_changes, kommnr_splits),
    )

    mock_validate_municipality_codes = mocker.patch(
        "ssb_befolkning_fagfunksjoner.municipality_codes.update_codes.validate_municipality_codes",
    )

    with pytest.warns(
        UserWarning,
        match=r"Municipality splits detected for codes:   old_code new_code\n0     1507     1508\n1     1507     1580",
    ):
        result = update_municipality_codes(original, 2024, validate=False)

    pd.testing.assert_series_equal(result, expected, check_names=False)
    mock_validate_municipality_codes.assert_not_called()


def test_validation_raises_invalid_code(
    mocker: MockerFixture,
    kommnr_changes: pd.DataFrame,
    empty_splits: pd.DataFrame,
    mock_valid_codes: set[str],
) -> None:
    original = pd.Series(["5401", "1111"])

    mocker.patch(
        "ssb_befolkning_fagfunksjoner.municipality_codes.update_codes.load_kommnr_changes",
        return_value=(kommnr_changes, empty_splits),
    )

    mocker.patch(
        "ssb_befolkning_fagfunksjoner.municipality_codes.validation.load_kommnr",
        return_value={code: {} for code in mock_valid_codes},
    )

    with pytest.raises(
        ValueError, match=r"Invalid municipality codes found: \['1111'\]"
    ):
        update_municipality_codes(original, 2024, validate=True)


def test_na_filled_with_0000(
    mocker: MockerFixture,
    kommnr_changes: pd.DataFrame,
    empty_splits: pd.DataFrame,
    mock_valid_codes: set[str],
) -> None:
    original = pd.Series(["0301", None])
    expected = pd.Series(["0301", "0000"])

    mocker.patch(
        "ssb_befolkning_fagfunksjoner.municipality_codes.update_codes.load_kommnr_changes",
        return_value=(kommnr_changes, empty_splits),
    )
    mocker.patch(
        "ssb_befolkning_fagfunksjoner.municipality_codes.validation.load_kommnr",
        return_value={code: {} for code in mock_valid_codes},
    )

    result = update_municipality_codes(original, 2024, validate=True)
    pd.testing.assert_series_equal(result, expected, check_names=False)


def test_recursive_mapping(
    mocker: MockerFixture, empty_splits: pd.DataFrame, mock_valid_codes: set[str]
) -> None:
    kommnr_changes = pd.DataFrame(
        {
            "old_code": ["1111", "2222"],
            "new_code": ["2222", "3333"],  # 1111 -> 2222 -> 3333
        }
    )

    mocker.patch(
        "ssb_befolkning_fagfunksjoner.municipality_codes.update_codes.load_kommnr_changes",
        return_value=(kommnr_changes, empty_splits),
    )
    mocker.patch(
        "ssb_befolkning_fagfunksjoner.municipality_codes.validation.load_kommnr",
        return_value={code: {} for code in mock_valid_codes.union({"3333"})},
    )

    original = pd.Series(["1111"])
    expected = pd.Series(["3333"])

    result = update_municipality_codes(original, 2024, validate=True)
    pd.testing.assert_series_equal(result, expected, check_names=False)
