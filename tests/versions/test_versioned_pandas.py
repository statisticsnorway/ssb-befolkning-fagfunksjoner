from collections.abc import Iterator
from unittest import mock

import pandas as pd
import pytest
from fsspec.spec import AbstractFileSystem
from upath import UPath

from ssb_befolkning_fagfunksjoner.versions import write_versioned_pandas


@pytest.fixture
def dummy_df() -> pd.DataFrame:
    return pd.DataFrame({"a": [1, 2], "b": [3, 4]})


@pytest.fixture
def mock_get_next_version_number() -> Iterator:
    with mock.patch(
        "ssb_befolkning_fagfunksjoner.versions.get_next_version_number"
    ) as mock_fn:
        yield mock_fn


@pytest.fixture
def mock_get_fileversions() -> Iterator:
    with mock.patch(
        "ssb_befolkning_fagfunksjoner.versions.get_fileversions"
    ) as mock_fn:
        yield mock_fn


@pytest.fixture
def patched_upath() -> Iterator:
    with mock.patch("ssb_befolkning_fagfunksjoner.versions.UPath") as mock_fn:
        yield mock_fn


@pytest.fixture
def patched_to_parquet() -> Iterator:
    with mock.patch.object(pd.DataFrame, "to_parquet") as mock_fn:
        yield mock_fn


@pytest.fixture
def mock_fs() -> mock.Mock:
    mock_fs = mock.Mock(spec=AbstractFileSystem)
    mock_fs.copy = mock.Mock()
    mock_fs.rm_file = mock.Mock()
    return mock_fs


@pytest.fixture
def mock_path(mock_fs: mock.Mock) -> mock.Mock:
    mock_path = mock.Mock(spec=UPath)
    mock_path.fs = mock_fs
    mock_path.parent = UPath("bucket/folders", protocol="gs")
    mock_path.stem = "testfile"
    return mock_path


@pytest.fixture
def mock_env(
    patched_upath,
    mock_get_next_version_number,
    mock_get_fileversions,
) -> tuple:
    return (
        patched_upath,
        mock_get_next_version_number,
        mock_get_fileversions,
    )


# Test first write (version == 1)
def test_first_write_only_latest_written(
    dummy_df: pd.DataFrame,
    mock_env: tuple,
    patched_to_parquet: Iterator,
    mock_path: mock.Mock,
) -> None:

    test_file = "gs://bucket/folders/testfile.parquet"

    # Mock internal functions used in write_versioned_pandas
    mock_upath, mock_get_next_version_number, mock_get_fileversions = mock_env

    # Patch return values for this test
    mock_upath.return_value = mock_path
    mock_get_next_version_number.return_value = 1
    mock_get_fileversions.return_value = []

    write_versioned_pandas(dummy_df, test_file, overwrite=False)

    # Should only write the unversioned file
    patched_to_parquet.assert_called_once_with(test_file)  # type: ignore


# Test version == 2 (promote + v2 + update latest)
def test_second_write_promotes_and_versions(
    dummy_df: pd.DataFrame,
    mock_env: tuple,
    patched_to_parquet: Iterator,
    mock_fs: mock.Mock,
    mock_path: mock.Mock,
) -> None:

    test_file = "gs://bucket/folders/testfile.parquet"
    existing_files = ["gs://bucket/folders/testfile.parquet"]

    # Mock internal functions used in write_versioned_pandas
    mock_upath, mock_get_next_version_number, mock_get_fileversions = mock_env

    # Patch return values for this test
    mock_upath.return_value = mock_path
    mock_get_next_version_number.return_value = 2
    mock_get_fileversions.return_value = existing_files

    write_versioned_pandas(dummy_df, test_file, overwrite=False)

    # Check copy and remove were called for promotion
    mock_fs.copy.assert_called_once_with(
        "gs://bucket/folders/testfile.parquet",
        "gs://bucket/folders/testfile_v1.parquet",
    )
    mock_fs.rm_file.assert_called_once_with("gs://bucket/folders/testfile.parquet")

    # Check two writes: v2 and updated latest
    assert patched_to_parquet.call_count == 2
    patched_to_parquet.assert_has_calls(
        [
            mock.call("gs://bucket/folder/testfile_v2.parquet"),
            mock.call("gs://bucket/folder/testfile.parquet"),
        ]
    )
