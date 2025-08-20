import pandas as pd
import pytest
from ssb_befolkning_fagfunksjoner.municipality_codes.update_codes import update_municipality_codes

@pytest.fixture
def kommnr_changes():
    # Example mappings: 5401 -> 5501, 3005 -> 3301
    return pd.DataFrame({
        "oldCode": ["5401", "3005"],
        "newCode": ["5501", "3301"],
    })

@pytest.fixture
def empty_splits():
    return pd.DataFrame({"oldCode": [], "newCode": []})

@pytest.fixture
def kommnr_splits():
    return pd.DataFrame({
        "oldCode": ["1507", "1507"],
        "newCode": ["1508", "1580"],
    })

@pytest.fixture
def mock_valid_codes():
    # The KLASS list you want to be valid at the validation date
    return {"0301", "5501", "4601", "1103", "3301", "1508", "1580", "0000"}


def test_update_and_validate(mocker, kommnr_changes: pd.DataFrame, empty_splits: pd.DataFrame, mock_valid_codes: set[str]):
    original = pd.Series(["0301", "5401", "4601", "1103", "3005"])
    expected = pd.Series(["0301", "5501", "4601", "1103", "3301"])

    mocker.patch(
        "ssb_befolkning_fagfunksjoner.municipality_codes.update_codes.load_kommnr_changes",
        return_value=(kommnr_changes, empty_splits)
    )

    mocker.patch(
        "ssb_befolkning_fagfunksjoner.municipality_codes.validation.load_kommnr",
        return_value={code: {} for code in mock_valid_codes}
    )

    mock_validate_municipality_codes = mocker.patch(
        "ssb_befolkning_fagfunksjoner.municipality_codes.update_codes.validate_municipality_codes",
    )

    result = update_municipality_codes(original_codes=original, year=2024, validate=True)

    pd.testing.assert_series_equal(result, expected, check_names=False)
    mock_validate_municipality_codes.assert_called_once_with(result, 2024)


def test_update_without_validation(mocker, kommnr_changes: pd.DataFrame, kommnr_splits: pd.DataFrame):
    original = pd.Series(["0301", "5401", "4601", "1103", "3005", "1507"])
    expected = pd.Series(["0301", "5501", "4601", "1103", "3301", "1507"])

    mocker.patch(
        "ssb_befolkning_fagfunksjoner.municipality_codes.update_codes.load_kommnr_changes",
        return_value=(kommnr_changes, kommnr_splits)
    )

    mock_validate_municipality_codes = mocker.patch(
        "ssb_befolkning_fagfunksjoner.municipality_codes.update_codes.validate_municipality_codes",
    )

    with pytest.warns(UserWarning, match=r"Municipality splits detected for codes: \['1507'\]"):
        result = update_municipality_codes(original, 2024, validate=False)
    
    pd.testing.assert_series_equal(result, expected, check_names=False)
    mock_validate_municipality_codes.assert_not_called()


def test_validation_raises_invalid_code(mocker, kommnr_changes: pd.DataFrame, empty_splits: pd.DataFrame, mock_valid_codes: set[str]):
    original = pd.Series(["5401", "1111"])

    mocker.patch(
        "ssb_befolkning_fagfunksjoner.municipality_codes.update_codes.load_kommnr_changes",
        return_value=(kommnr_changes, empty_splits)
    )

    mocker.patch(
        "ssb_befolkning_fagfunksjoner.municipality_codes.validation.load_kommnr",
        return_value={code: {} for code in mock_valid_codes}
    )

    with pytest.raises(ValueError, match=r"Invalid municipality codes found: \['1111'\]"):
        update_municipality_codes(original, 2024, validate=True)


def test_na_filled_with_0000(mocker, kommnr_changes: pd.DataFrame, empty_splits: pd.DataFrame, mock_valid_codes: set[str]):
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


def test_recursive_mapping(mocker, empty_splits, mock_valid_codes):
    kommnr_changes = pd.DataFrame({
        "oldCode": ["1111", "2222"],
        "newCode": ["2222", "3333"],   # 1111 -> 2222 -> 3333
    })

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
