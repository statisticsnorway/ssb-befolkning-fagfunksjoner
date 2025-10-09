import pandas as pd
import pytest
from pytest_mock import MockerFixture
from pytest_mock.plugin import MockType
from upath import UPath

from ssb_befolkning_fagfunksjoner.versions.versions import write_versioned_pandas

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
def mock_diff_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "id": ["A", "B", "C"],
            "value": [2, 4, 6],
        }
    )


@pytest.fixture
def mock_writers(mocker: MockerFixture) -> dict[str, MockType]:
    return {
        "promote": mocker.patch(
            "ssb_befolkning_fagfunksjoner.versions.versions.promote_unversioned_to_v1",
            autospec=True,
        ),
        "create": mocker.patch(
            "ssb_befolkning_fagfunksjoner.versions.versions.create_versioned_file",
            autospec=True,
        ),
        "update": mocker.patch(
            "ssb_befolkning_fagfunksjoner.versions.versions.update_latest_file",
            autospec=True,
        ),
    }


# ------------------------------------------------------------------------
# Test 1: first write (next_version == 1) → only latest is updated
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
        return_value=1,
    )

    input_path = "bucket/folder/file.parquet"
    mock_resolve_path = mocker.patch(
        "ssb_befolkning_fagfunksjoner.versions.versions.resolve_path",
        return_value=UPath(input_path),
    )
    resolved_path: UPath = mock_resolve_path.return_value

    write_versioned_pandas(df=mock_df, filepath=input_path)
    mock_resolve_path.assert_called_once_with(input_path)

    mock_writers["update"].assert_called_once_with(
        df=mock_df, parent=resolved_path.parent, stem=resolved_path.stem
    )
    mock_writers["create"].assert_not_called()
    mock_writers["promote"].assert_not_called()


# ------------------------------------------------------------------------
# Test 2a: second write (next_version == 2), latest missing -> ValueError
# ------------------------------------------------------------------------


def test_second_write_latest_missing_raises(
    mocker: MockerFixture,
    mock_df: pd.DataFrame,
    mock_writers: dict[str, MockType],
) -> None:
    mocker.patch(
        "ssb_befolkning_fagfunksjoner.versions.versions.get_next_version_number",
        return_value=2,
    )

    input_path = "bucket/folder/file.parquet"
    mock_resolve_path = mocker.patch(
        "ssb_befolkning_fagfunksjoner.versions.versions.resolve_path",
        return_value=UPath(input_path),
    )
    resolved = mock_resolve_path.return_value

    mocker.patch.object(type(resolved), "exists", return_value=False)

    with pytest.raises(ValueError, match=r"Expected '.*\.parquet' to exist"):
        write_versioned_pandas(df=mock_df, filepath=input_path)

    mock_writers["promote"].assert_not_called()
    mock_writers["create"].assert_not_called()
    mock_writers["update"].assert_not_called()


# ------------------------------------------------------------------------
# Test 2b: second write (next_version == 2), latest exists + identical -> skip all writes
# ------------------------------------------------------------------------


def test_second_write_identical_skips(
    mocker: MockerFixture,
    mock_df: pd.DataFrame,
    mock_diff_df: pd.DataFrame,
    mock_writers: dict[str, MockType],
):
    mocker.patch(
        "ssb_befolkning_fagfunksjoner.versions.versions.get_next_version_number",
        return_value=2,
    )

    input_path = "bucket/folder/file.parquet"
    mock_resolve_path = mocker.patch(
        "ssb_befolkning_fagfunksjoner.versions.versions.resolve_path",
        return_value=UPath(input_path),
    )
    resolved: UPath = mock_resolve_path.return_value

    mocker.patch.object(type(resolved), "exists", return_value=True)  # latest exists
    mocker.patch("pandas.read_parquet", return_value=mock_df)  # identical content

    write_versioned_pandas(df=mock_df, filepath=input_path)

    mock_writers["promote"].assert_not_called()
    mock_writers["create"].assert_not_called()
    mock_writers["update"].assert_not_called()


# ------------------------------------------------------------------------
# Test 2c: second write (next_version == 2), latest exists + different -> promote, create(v2), update
# ------------------------------------------------------------------------


def test_second_write_different(
    mocker: MockerFixture,
    mock_df: pd.DataFrame,
    mock_diff_df: pd.DataFrame,
    mock_writers: dict[str, MockType],
):
    mocker.patch(
        "ssb_befolkning_fagfunksjoner.versions.versions.get_next_version_number",
        return_value=2,
    )

    input_path = "bucket/folder/file.parquet"
    mock_resolve_path = mocker.patch(
        "ssb_befolkning_fagfunksjoner.versions.versions.resolve_path",
        return_value=UPath(input_path),
    )
    resolved: UPath = mock_resolve_path.return_value

    mocker.patch.object(type(resolved), "exists", return_value=True)  # latest exists
    mocker.patch("pandas.read_parquet", return_value=mock_diff_df)  # different content

    write_versioned_pandas(df=mock_df, filepath=input_path)

    mock_writers["promote"].assert_called_once_with(
        parent=resolved.parent, stem=resolved.stem
    )
    mock_writers["create"].assert_called_once_with(
        df=mock_df, parent=resolved.parent, stem=resolved.stem, version=2
    )
    mock_writers["update"].assert_called_once_with(
        df=mock_df, parent=resolved.parent, stem=resolved.stem
    )


# ------------------------------------------------------------------------
# Test 2d: second write (next_version == 2), latest exists but read fails -> ValueError
# ------------------------------------------------------------------------


def test_second_write_read_failure_raises(
    mocker: MockerFixture,
    mock_df: pd.DataFrame,
    mock_writers: dict[str, MockType],
) -> None:
    mocker.patch(
        "ssb_befolkning_fagfunksjoner.versions.versions.get_next_version_number",
        return_value=2,
    )

    input_path = "bucket/folder/file.parquet"
    mock_resolve_path = mocker.patch(
        "ssb_befolkning_fagfunksjoner.versions.versions.resolve_path",
        return_value=UPath(input_path),
    )
    resolved: UPath = mock_resolve_path.return_value

    mocker.patch.object(type(resolved), "exists", return_value=True)  # latest exists
    mocker.patch(
        "pandas.read_parquet", side_effect=ValueError("boom")
    )  # different content

    with pytest.raises(ValueError, match=r"Failed to read existing version"):
        write_versioned_pandas(df=mock_df, filepath=input_path)

    mock_writers["promote"].assert_not_called()
    mock_writers["create"].assert_not_called()
    mock_writers["update"].assert_not_called()


# ------------------------------------------------------------------------
# Test 3a: subsequent write (next_version > 2), latest exists + identical -> skip
# ------------------------------------------------------------------------


def test_subsequent_write_identical_skips(
    mocker: MockerFixture,
    mock_df: pd.DataFrame,
    mock_writers: dict[str, MockType],
) -> None:
    mocker.patch(
        "ssb_befolkning_fagfunksjoner.versions.versions.get_next_version_number",
        return_value=3,
    )

    input_path = "bucket/folder/file.parquet"
    mock_resolve_path = mocker.patch(
        "ssb_befolkning_fagfunksjoner.versions.versions.resolve_path",
        return_value=UPath(input_path),
    )
    resolved: UPath = mock_resolve_path.return_value

    mocker.patch.object(type(resolved), "exists", return_value=True)
    mocker.patch("pandas.read_parquet", return_value=mock_df)

    write_versioned_pandas(df=mock_df, filepath=input_path)

    mock_writers["promote"].assert_not_called()
    mock_writers["create"].assert_not_called()
    mock_writers["update"].assert_not_called()


# ------------------------------------------------------------------------
# Test 3b: subsequent write (next version > 2), latest exists + different -> create(vN), update
# ------------------------------------------------------------------------


def test_subsequent_write_different_creates_and_updates(
    mocker: MockerFixture,
    mock_df: pd.DataFrame,
    mock_df_diff: pd.DataFrame,
    mock_writers: dict[str, MockType],
) -> None:
    next_version = 3
    mocker.patch(
        "ssb_befolkning_fagfunksjoner.versions.versions.get_next_version_number",
        return_value=next_version,
    )

    input_path = "bucket/folder/file.parquet"
    mock_resolve_path = mocker.patch(
        "ssb_befolkning_fagfunksjoner.versions.versions.resolve_path",
        return_value=UPath(input_path),
    )
    resolved: UPath = mock_resolve_path.return_value

    mocker.patch.object(type(resolved), "exists", return_value=True)
    mocker.patch("pandas.read_parquet", return_value=mock_df_diff)

    write_versioned_pandas(df=mock_df, filepath=input_path)

    mock_writers["promote"].assert_not_called()
    mock_writers["create"].assert_called_once_with(
        df=mock_df, parent=resolved.parent, stem=resolved.stem, version=next_version
    )
    mock_writers["update"].assert_called_once_with(
        df=mock_df, parent=resolved.parent, stem=resolved.stem
    )


# ------------------------------------------------------------------------
# Test 4: invalid input path (vN in stem) -> ValueError
# ------------------------------------------------------------------------


def test_invalid_versioned_filepath(
    mocker: MockerFixture, mock_df: pd.DataFrame, mock_writers: dict[str, MockType]
) -> None:
    input_path = "bucket/folder/file_v3.parquet"
    mocker.patch(
        "ssb_befolkning_fagfunksjoner.versions.versions.resolve_path",
        return_value=UPath(input_path),
    )

    with pytest.raises(ValueError, match=r"Detected versioning"):
        write_versioned_pandas(df=mock_df, filepath=input_path)

    mock_writers["promote"].assert_not_called()
    mock_writers["create"].assert_not_called()
    mock_writers["update"].assert_not_called()
