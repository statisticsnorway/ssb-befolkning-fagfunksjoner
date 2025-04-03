from unittest.mock import Mock


from unittest.mock import Mock


from unittest.mock import AsyncMock, MagicMock


from typing import Any, Generator


from unittest.mock import AsyncMock, MagicMock


from unittest import mock

import pandas as pd
import pytest
from upath import UPath

from ssb_befolkning_fagfunksjoner.versions import write_versioned_pandas


@pytest.fixture
def dummy_df() -> pd.DataFrame:
    return pd.DataFrame({"a": [1, 2], "b": [3, 4]})


@pytest.fixture
def patched_env() -> Generator[tuple[MagicMock | AsyncMock, MagicMock | AsyncMock, MagicMock | AsyncMock], Any, None]:
    with mock.patch(
        "ssb_befolkning_fagfunksjoner.versions.UPath"
    ) as mock_upath, mock.patch(
        "ssb_befolkning_fagfunksjoner.versions.get_next_version_number"
    ) as mock_get_next_version_number, mock.patch(
        "ssb_befolkning_fagfunksjoner.versions.get_fileversions"
    ) as mock_get_fileversions:
        yield mock_upath, mock_get_next_version_number, mock_get_fileversions


@pytest.fixture
def patched_to_parquet() -> Generator[MagicMock | AsyncMock, Any, None]:
    with mock.patch.object(pd.DataFrame, "to_parquet") as mock_to_parquet:
        yield mock_to_parquet


@pytest.fixture
def patched_fs() -> Mock:
    mock_fs: Mock = mock.Mock()     # Mock FileClient fs
    mock_fs.copy = mock.Mock()      # Mock return for fs.copy
    mock_fs.rm_file = mock.Mock()   # Mock return for fs.rm_file
    return mock_fs


# Test first write (version == 1)
def test_first_write_only_latest_written(dummy_df, patched_env, patched_to_parquet) -> None:
    mock_upath, mock_get_version, mock_get_versions = patched_env
    mock_path = mock.Mock()
    mock_path.fs = mock.Mock()
    mock_path.parent = UPath("mock/parent", protocol="gs")
    mock_path.stem = "testfile"
    mock_upath.return_value = mock_path

    mock_get_version.return_value = 1
    mock_get_versions.return_value = []

    write_versioned_pandas(dummy_df, "gs://bucket/testfile.parquet", overwrite=False)

    # Should only write the unversioned file
    patched_to_parquet.assert_called_once_with("gs://mock/parent/testfile.parquet")


# Test version == 2 (promote + v2 + update latest)
def test_second_write_promotes_and_versions(
    dummy_df, patched_env, patched_to_parquet, patched_fs
) -> None:
    mock_upath, mock_get_version, mock_get_versions = patched_env
    mock_path = mock.Mock()
    mock_path.fs = patched_fs
    mock_path.parent = UPath("mock/parent", protocol="gs")
    mock_path.stem = "testfile"
    mock_upath.return_value = mock_path

    mock_get_version.return_value = 2
    mock_get_versions.return_value = []

    write_versioned_pandas(dummy_df, "gs://bucket/testfile.parquet", overwrite=False)

    # Check copy and remove were called for promotion
    patched_fs.copy.assert_called_once_with(
        "gs://mock/parent/testfile.parquet", "gs://mock/parent/testfile_v1.parquet"
    )
    patched_fs.rm_file.assert_called_once_with("gs://mock/parent/testfile.parquet")

    # Check two writes: v2 and updated latest
    assert patched_to_parquet.call_count == 2
    calls = [
        mock.call("gs://mock/parent/testfile_v2.parquet"),
        mock.call("gs://mock/parent/testfile.parquet"),
    ]
    patched_to_parquet.assert_has_calls(calls, any_order=False)


# Test version > 2
def test_later_write_adds_version(dummy_df, patched_env, patched_to_parquet) -> None:
    mock_upath, mock_get_version, mock_get_versions = patched_env
    mock_path = mock.Mock()
    mock_path.fs = mock.Mock()
    mock_path.parent = UPath("mock/parent", protocol="gs")
    mock_path.stem = "testfile"
    mock_upath.return_value = mock_path

    mock_get_version.return_value = 5
    mock_get_versions.return_value = []

    write_versioned_pandas(dummy_df, "gs://bucket/testfile.parquet", overwrite=False)

    # Should write v5 and update latest
    assert patched_to_parquet.call_count == 2
    calls = [
        mock.call("gs://mock/parent/testfile_v5.parquet"),
        mock.call("gs://mock/parent/testfile.parquet"),
    ]
    patched_to_parquet.assert_has_calls(calls, any_order=False)


# Test input with version in name
def test_input_with_version_suffix_raises(dummy_df, patched_env) -> None:
    mock_upath, _, _ = patched_env
    mock_path = mock.Mock()
    mock_path.fs = mock.Mock()
    mock_path.parent = UPath("mock/parent", protocol="gs")
    mock_path.stem = "testfile_v2"
    mock_upath.return_value = mock_path

    with pytest.raises(ValueError, match="Detected versioning in function parameter"):
        write_versioned_pandas(
            dummy_df, "gs://bucket/testfile_v2.parquet", overwrite=False
        )
