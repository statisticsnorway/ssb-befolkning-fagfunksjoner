from collections.abc import Generator
from unittest import mock
from unittest.mock import Mock

import pandas as pd
import pytest
from upath import UPath

from ssb_befolkning_fagfunksjoner.versions.versions import write_versioned_pandas


@pytest.fixture
def dummy_df() -> pd.DataFrame:
    return pd.DataFrame({"a": [1, 2], "b": [3, 4]})


@pytest.fixture
def mock_get_next_version_number() -> Generator[Mock, None, None]:
    with mock.patch(
        "ssb_befolkning_fagfunksjoner.versions._versions.get_next_version_number"
    ) as mock_fn:
        yield mock_fn


@pytest.fixture
def mock_resolve_path() -> Generator[tuple[UPath, Mock], None, None]:
    with mock.patch(
        "ssb_befolkning_fagfunksjoner.versions.versions._versions.resolve_path"
    ) as mock_fn:
        mock_fn.return_value = UPath("gs://bucket/folders/testfile.parquet")
        yield mock_fn


@pytest.fixture
def mock_to_parquet() -> Generator[Mock, None, None]:
    with mock.patch.object(pd.DataFrame, "to_parquet") as mock_fn:
        yield mock_fn


@pytest.mark.parametrize(
    "input_filepath, resolved_upath",
    [
        (
            "gs://bucket/folder/file.parquet",
            UPath("gs://bucket/folder/file.parquet", protocol="gs"),
        ),
        (
            "ssb-bucket-data-dev/folder/file.parquet",
            UPath("gs://ssb-bucket-data-dev/folder/file.parquet", protocol="gs"),
        ),
        ("/buckets/demo/file.parquet", UPath("/buckets/demo/file.parquet")),
    ],
)
def test_write_unversioned(
    dummy_df: pd.DataFrame,
    mock_resolve_path: Mock,
    mock_to_parquet: Mock,
    mock_get_next_version_number: Mock,
    input_filepath: str,
    resolved_upath: UPath,
) -> None:
    """Test that write_versioned_pandas writes only the unversioned file when no existing versions are present."""
    expected_write_path = resolved_upath.parent / f"{resolved_upath.stem}.parquet"

    mock_resolve_path.return_value = resolved_upath
    mock_get_next_version_number.return_value = 1  # assert no versioned file exists yet

    write_versioned_pandas(dummy_df, input_filepath)

    # Check resolve_path() call
    mock_resolve_path.assert_called_once_with(input_filepath)

    # Check input parameters of to_parquet() call
    mock_to_parquet.assert_called_once()
    call_path = mock_to_parquet.call_args[0][0]
    assert isinstance(call_path, UPath)  # parameter is UPath object
    assert str(call_path) == str(expected_write_path)  # has expected structure


@pytest.mark.parametrize("equal, expect_write", [(False, True), (True, False)])
def test_write_promotion_and_update(
    dummy_df: pd.DataFrame,
    mock_resolve_path: Mock,
    mock_get_next_version_number: Mock,
    mock_to_parquet: Mock,
    equal: bool,
    expect_write: bool,
) -> None:
    """Test version 2 write behavior.

    - If the existing file equals the new DataFrame:
        - Skip promotion and writing.

    - If the existing file differs:
        - Promote the unversioned file to _v1 using UPath.rename().
        - Write the new version to _v2.
        - Update the unversioned file with the new data.
    """
    input_filepath = "gs://bucket/folders/testfile.parquet"
    resolved_upath = UPath(input_filepath)

    mock_resolve_path.return_value = resolved_upath
    mock_get_next_version_number.return_value = 2

    # Construct expected paths
    parent = resolved_upath.parent
    stem = resolved_upath.stem
    unversioned_path = parent / f"{stem}.parquet"
    promoted_path = parent / f"{stem}_v1.parquet"
    versioned_path = parent / f"{stem}_v2.parquet"

    # Patch real UPath calls
    with (
        mock.patch.object(type(resolved_upath), "rename") as mock_rename,
        mock.patch.object(type(unversioned_path), "exists", return_value=True),
        mock.patch("pandas.read_parquet") as mock_read_parquet,
    ):
        mock_existing_df = mock.MagicMock()
        mock_read_parquet.return_value = mock_existing_df
        mock_existing_df.equals.return_value = equal

        write_versioned_pandas(dummy_df, input_filepath)

    if expect_write:
        mock_rename.assert_called_once_with(target=promoted_path)
        mock_to_parquet.assert_has_calls(
            [mock.call(versioned_path), mock.call(unversioned_path)]
        )
    else:
        mock_rename.assert_not_called()
        mock_to_parquet.assert_not_called()


def test_rejects_versioned_filepath(dummy_df: pd.DataFrame) -> None:
    versioned_input = "gs://bucket/folder/myfile_v2.parquet"
    with pytest.raises(ValueError, match="Detected versioning in function parameter"):
        write_versioned_pandas(dummy_df, versioned_input)
