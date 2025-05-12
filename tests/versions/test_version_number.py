from typing import Any
from unittest import mock

from ssb_befolkning_fagfunksjoner.versions.versions import get_next_version_number


def test_get_next_version_number_with_existing_versions() -> None:
    test_filepath = "gs://bucket/folder/file.parquet"
    mock_files = [
        "gs://bucket/folder/file.parquet",
        "gs://bucket/folder/file_v1.parquet",
        "gs://bucket/folder/file_v2.parquet",
        "gs://bucket/folder/file_v3.parquet",
    ]

    expected_next_version = 4

    with mock.patch(
        "ssb_befolkning_fagfunksjoner.versions.get_fileversions",
        return_value=mock_files,
    ):
        result = get_next_version_number(test_filepath)
        assert result == expected_next_version


def test_get_next_version_number_no_existing_files() -> None:
    test_filepath = "gs://bucket/folder/file.parquet"
    mock_files: list[Any] = []

    expected_next_version = 1

    with mock.patch(
        "ssb_befolkning_fagfunksjoner.versions.get_fileversions",
        return_value=mock_files,
    ):
        result = get_next_version_number(test_filepath)
        assert result == expected_next_version
