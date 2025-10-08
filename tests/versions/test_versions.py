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
            "value": [1, 2, 3],
        }
    )

@pytest.fixture
def mock_resolved_path(mocker: MockerFixture) -> UPath:
    resolved = UPath("gs://my-bucket/folder/file.parquet")
    mocker.patch(
        "ssb_befolkning_fagfunksjoner.versions.versions.resolve_path",
        return_value=resolved
    )
    return resolved

@pytest.fixture
def mock_promote_unversioned_to_v1(mocker: MockerFixture) -> MockType:
    return mocker.patch(
        "ssb_befolkning_fagfunksjoner.versions.versions.promote_unversioned_to_v1"
    )

@pytest.fixture
def mock_create_versioned_file(mocker: MockerFixture) -> MockType:
    return mocker.patch(
        "ssb_befolkning_fagfunksjoner.versions.versions.create_versioned_file"
    )

@pytest.fixture
def mock_update_latest_file(mocker: MockerFixture) -> MockType:
    return mocker.patch(
        "ssb_befolkning_fagfunksjoner.versions.versions.update_latest_file"
    )

# ------------------------------------------------------------------------
# Test 1: function triggers 'update_latest_file' and nothing else if next_version_number = 1
# ------------------------------------------------------------------------

def test_write_versioned_pandas_first_write(
    mocker: MockerFixture,
    mock_df: pd.DataFrame,
    mock_resolved_path: UPath,
    mock_promote_unversioned_to_v1: MockType,
    mock_create_versioned_file: MockType,
    mock_update_latest_file: MockType,
) -> None:
    """If no other file exists in write path, then 'next_version_number' = 1 and file is written as-is."""
    # Patch functions called in write_versioned_pandas()
    mocker.patch(
        "ssb_befolkning_fagfunksjoner.versions.versions.get_next_version_number",
        return_value=1
    )
    
    write_versioned_pandas(df=mock_df, filepath="bucket/folder/file.parquet")

    mock_update_latest_file.assert_called_once_with(
        df=mock_df, parent=mock_resolved_path.parent, stem=mock_resolved_path.stem
    )
    mock_create_versioned_file.assert_not_called()
    mock_promote_unversioned_to_v1.assert_not_called()
