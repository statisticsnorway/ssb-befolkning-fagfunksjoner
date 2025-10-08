from datetime import date
import pandas as pd
import pytest
from pytest_mock import MockerFixture
import klass

from ssb_befolkning_fagfunksjoner.kommnr.changes import get_kommnr_changes


# ------------------------------------------------------------------------
# Common fixtures (used by multiple tests)
# ------------------------------------------------------------------------

@pytest.fixture
def mock_klass_classification(mocker: MockerFixture):
    return mocker.patch(
        "ssb_befolkning_fagfunksjoner.kommnr.changes.klass.KlassClassification",
        return_value=mocker.Mock(spec=klass.KlassClassification)
    )

@pytest.fixture
def mock_klass_change_mapping() -> pd.Series:
    """
    Mocks klass change mapping with:
        - one split ("1507" -> "1508"/"1580"), 
        - two changes ("5401" -> "5501"; "3005" -> "3301"), 
        - one unchanged code ("0301").
    
    Index is old_code and value is new_code.
    """
    return pd.Series(
        ["1508", "1580", "5501", "3301", "0301"],
        index = ["1507", "1507", "5401", "3005", "0301"],
        name=None,
    )


# ------------------------------------------------------------------------
# Test 1: divide series into DataFrames with splits and changes
# ------------------------------------------------------------------------

def test_get_klass_change_mapping(
    mocker: MockerFixture,
    mock_klass_change_mapping: pd.Series,
) -> None:
    expected_changes = pd.DataFrame({"old_code": ["5401", "3005"], "new_code": ["5501", "3301"]})
    expected_splits = pd.DataFrame({"old_code": ["1507", "1507"], "new_code": ["1508", "1580"]})
    
    mocker.patch(
        "ssb_befolkning_fagfunksjoner.kommnr.changes.get_klass_change_mapping",
        return_value=mock_klass_change_mapping
    )

    changes, splits = get_kommnr_changes(
        from_date="1980-01-01", to_date="2024-01-01", target_date="2024-01-01"
    )

    pd.testing.assert_frame_equal(
        changes.sort_values(["old_code", "new_code"]).reset_index(drop=True),
        expected_changes.sort_values(["old_code", "new_code"]).reset_index(drop=True),
        check_like=True,
    )
    pd.testing.assert_frame_equal(
        splits.sort_values(["old_code", "new_code"]).reset_index(drop=True),
        expected_splits.sort_values(["old_code", "new_code"]).reset_index(drop=True),
        check_like=True,
    )


# ------------------------------------------------------------------------
# Test 2: Date string parsing
# ------------------------------------------------------------------------
cases = [
    (
        ["1980-01-01", "2024-01-01", None],
        [date(1980, 1, 1), date(2024, 1, 1), date(2024, 1, 1)],
        False,
    ),
    (
        ["1980-01-01", None, "2023-01-01"],
        [date(1980, 1, 1), None, date(2023, 1, 1)],
        False,
    ),
    (
        [date(1980, 1, 1), date(2020, 1, 1), date(2020, 1, 1)],
        [date(1980, 1, 1), date(2020, 1, 1), date(2020, 1, 1)],
        False,
    ),
    (
        ["2000-13-40", None, None],
        [],
        True,
    ),
    (
        ["1980-01-01", 123, None],
        ["1980-01-01", 123, 123],
        False,
    )
]

@pytest.mark.parametrize("input, expected_output, errors", cases)
def test_date_parsing_and_default(
    mocker: MockerFixture,
    mock_klass_change_mapping: pd.Series,
    inputs: list,
    expected_output: list, 
    errors: bool
) -> None:
    """Verify normalisation/defaulting of from_date/to_date/target_date in get_kommnr_changes."""
    mock_get_klass_change_mapping = mocker.patch(
        "ssb_befolkning_fagfunksjoner.kommnr.changes.get_klass_change_mapping",
        return_value=mock_klass_change_mapping
    )

    if errors:
        with pytest.raises(ValueError):
            get_kommnr_changes(*inputs)
        mock_get_klass_change_mapping.assert_not_called()
        return

    _changes, _splits = get_kommnr_changes(*inputs)

    # Verify call arguments: both from_date/to_date/target_date are datetime.date
    _args, kwargs = mock_get_klass_change_mapping.call_args

    assert kwargs.get("from_date") == expected_output[0]
    assert kwargs.get("to_date") == expected_output[1]
    assert kwargs.get("target_date") == expected_output[2]
