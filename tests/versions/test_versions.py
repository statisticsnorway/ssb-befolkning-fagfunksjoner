from upath.core import UPath


from pytest_mock.plugin import MockType


from pytest_mock.plugin import MockType


from pytest_mock.plugin import MockType


import pytest
import pandas as pd 
from pytest_mock import MockerFixture
from upath import UPath

from ssb_befolkning_fagfunksjoner.versions.versions import write_versioned_pandas

# tests: 
# - if no files in path, trigger write (unversioned)
# - if one existing file, renames, and writes as v2 and unversioned
# - otherwise error
# throws error if versioning in input filename
# take next_version_number as given :) 
# if trying to save dataframe which is equal, then does not write

# ------------------------------------------------------------------------
# Common fixtures
# ------------------------------------------------------------------------

@pytest.fixture
def mock_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "id": ["A", "B", "C"],
            "value": [1, 2, 3],
        }
    )

@pytest.fixture
def mock_existing_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "id": ["A", "B", "C"],
            "value": [2, 4, 6],
        }
    )

@pytest.fixture
def mock_writers(mocker: MockerFixture) -> dict[str, MockType]:
    return {
        "promote": mocker.patch("ssb_befolkning_fagfunksjoner.versions.versions.promote_unversioned_to_v1"),
        "create": mocker.patch("ssb_befolkning_fagfunksjoner.versions.versions.create_versioned_file"),
        "update": mocker.patch("ssb_befolkning_fagfunksjoner.versions.versions.update_latest_file"),
    }


# ------------------------------------------------------------------------
# Test 1: function triggers 'update_latest_file' and nothing else if next_version_number = 1
# ------------------------------------------------------------------------

def test_write_versioned_pandas_first_write(
    mocker: MockerFixture,
    mock_df: pd.DataFrame,
    mock_writers: dict[str, MockType],
) -> None:
    """If no other file exists in write path, then 'next_version_number' = 1 and file is written as-is."""
    # Patch functions called in write_versioned_pandas()
    mocker.patch(
        "ssb_befolkning_fagfunksjoner.versions.versions.get_next_version_number",
        return_value=1
    )

    input_path = "bucket/folder/file.parquet"
    mock_resolve_path = mocker.patch(
        "ssb_befolkning_fagfunksjoner.versions.versions.resolve_path",
        return_value=UPath(input_path)
    )
    resolved_path: UPath = mock_resolve_path.return_value

    write_versioned_pandas(df=mock_df, filepath=input_path)
    mock_resolve_path.assert_called_once_with(input_path)
    
    mock_writers["update"].assert_called_once_with(df=mock_df, parent=resolved_path.parent, stem=resolved_path.stem)
    mock_writers["create"].assert_not_called()
    mock_writers["promote"].assert_not_called()


# ------------------------------------------------------------------------
# Test 2: function triggers promote_unversioned_to_v1, create_versioned_file, and update_latest_file when unequal existing df exists and next_version_number = 2
# ------------------------------------------------------------------------

def test_write_versioned_pandas_second_write(
    mocker: MockerFixture,
    mock_df: pd.DataFrame,
    mock_writers: dict[str, MockType],
) -> None:
    mocker.patch(
        "ssb_befolkning_fagfunksjoner.versions.versions.get_next_version_number",
        return_value=2
    )

    input_path = "bucket/folder/file.parquet"
    mock_resolve_path = mocker.patch(
        "ssb_befolkning_fagfunksjoner.versions.versions.resolve_path",
        return_value=UPath(input_path)
    )
    resolved_path: UPath = mock_resolve_path.return_value
    latest_path: UPath = resolved_path.parent / f"{resolved_path.stem}.parquet"

    def exists_side_effect(self: UPath) -> bool:
        return self == latest_path

    mocker.patch("upath.UPath.exists", side_effect=exists_side_effect)

    with pytest.raises(ValueError, match=r"Expected '.*\.parquet' to exist"):
        write_versioned_pandas(df=mock_df, filepath=input_path)

    mock_writers["update"].assert_not_called()
    mock_writers["create"].assert_not_called()
    mock_writers["promote"].assert_not_called()


# ------------------------------------------------------------------------
# Test 3: 
# ------------------------------------------------------------------------

def test_write_versioned_pandas_identical_skip(
    mocker: MockerFixture,
    mock_df,
    mock_writers,
):
    mocker.patch(
        "ssb_befolkning_fagfunksjoner.versions.versions.get_next_version_number",
        return_value=2
    )

    


# ------------------------------------------------------------------------
# Test 3: Throws error if version in input filepath
# ------------------------------------------------------------------------

def test_write_versioned_pandas_version_error(
    mocker: MockerFixture,
    mock_df: pd.DataFrame,
) -> None:

    input_path = "bucket/folder/file_v1.parquet"
    mock_resolve_path = mocker.patch(
        "ssb_befolkning_fagfunksjoner.versions.versions.resolve_path",
        return_value=UPath(input_path)
    )
 
    with pytest.raises(ValueError):
        write_versioned_pandas(df=mock_df, filepath=input_path)
    mock_resolve_path.assert_called_once_with(input_path)
