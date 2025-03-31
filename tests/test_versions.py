from unittest.mock import patch, MagicMock


def test_deconstruct_file_pattern():
    from src.ssb_befolkning_fagfunksjoner.versions import deconstruct_file_pattern

    filepath = "gs://bucket/folder/file_v1.parquet"
    expected = "gs://bucket/folder/file*.parquet"
    result = deconstruct_file_pattern(filepath)
    assert result == expected


def test_get_version_number_from_filepath():
    from src.ssb_befolkning_fagfunksjoner.versions import (
        get_version_number_from_filepath,
    )

    # File with a version suffix
    filepath = "gs://bucket/folder/file_v2.parquet"
    assert get_version_number_from_filepath(filepath) == 2

    # File without a version suffix
    filepath = "gs://bucket/folder/file.parquet"
    assert get_version_number_from_filepath(filepath) is None

    # File with invalid naming
    filepath = "gs://bucket/folder/file_v2_v3.parquet"
    try:
        get_version_number_from_filepath(filepath)
    except ValueError as e:
        assert (
            str(e)
            == "Multiple '_v' occurrences found in 'file_v2_v3'. Filename does not follow the expected convention."
        )


@patch("src.ssb_befolkning_fagfunksjoner.versions.get_fileversions")
def test_get_next_version_number(mock_get_fileversions):
    from src.ssb_befolkning_fagfunksjoner.versions import get_next_version_number

    # Mock the return value of get_fileversions
    mock_get_fileversions.return_value = [
        "gs://bucket/folder/file.parquet",
        "gs://bucket/folder/file_v1.parquet",
        "gs://bucket/folder/file_v2.parquet",
    ]

    # Test the next version number
    filepath = "gs://bucket/folder/file.parquet"
    assert get_next_version_number(filepath) == 3


@patch("src.ssb_befolkning_fagfunksjoner.versions.get_fileversions")
@patch("src.ssb_befolkning_fagfunksjoner.versions.get_next_version_number")
@patch("src.ssb_befolkning_fagfunksjoner.versions.UPath")
@patch("pandas.DataFrame.to_parquet")
def test_write_versioned_pandas_existing_v1(
    mock_to_parquet,
    mock_upath,
    mock_get_next_version_number,
    mock_get_fileversions,
):
    from src.ssb_befolkning_fagfunksjoner.versions import write_versioned_pandas
    import pandas as pd

    mock_get_fileversions.return_value = ["gs://bucket/folder/file.parquet"]
    mock_get_next_version_number.return_value = 2
    df = pd.DataFrame({"col1": [1, 2, 3]})

    mock_path = MagicMock()
    mock_path.stem = "file"
    mock_path.suffix = ".parquet"
    mock_path.name = "file.parquet"
    mock_path.parent.__truediv__.side_effect = lambda x: f"gs://bucket/folder/{x}"
    mock_path.fs.copy = MagicMock()
    mock_path.fs.rm_file = MagicMock()
    mock_upath.return_value = mock_path

    write_versioned_pandas(df, "gs://bucket/folder/file.parquet", overwrite=False)

    mock_to_parquet.assert_any_call("gs://bucket/folder/file_v2.parquet")
    mock_to_parquet.assert_any_call("gs://bucket/folder/file.parquet")

    mock_path.fs.copy.assert_called_once_with(
        "gs://bucket/folder/file.parquet", "gs://bucket/folder/file_v1.parquet", overwrite=True
    )
    mock_path.fs.rm_file.assert_called_once_with("gs://bucket/folder/file.parquet")


@patch("src.ssb_befolkning_fagfunksjoner.versions.get_fileversions")
@patch("src.ssb_befolkning_fagfunksjoner.versions.get_next_version_number")
@patch("src.ssb_befolkning_fagfunksjoner.versions.UPath")
@patch("pandas.DataFrame.to_parquet")
def test_write_versioned_pandas_no_existing_files(
    mock_to_parquet,
    mock_upath,
    mock_get_next_version_number,
    mock_get_fileversions,
):
    from src.ssb_befolkning_fagfunksjoner.versions import write_versioned_pandas
    import pandas as pd

    mock_get_fileversions.return_value = []
    mock_get_next_version_number.return_value = 1
    df = pd.DataFrame({"col1": [1, 2, 3]})

    mock_path = MagicMock()
    mock_path.stem = "file"
    mock_path.suffix = ".parquet"
    mock_path.name = "file.parquet"
    mock_path.parent.__truediv__.side_effect = lambda x: f"gs://bucket/folder/{x}"
    mock_path.fs.copy = MagicMock()
    mock_path.fs.rm_file = MagicMock()
    mock_upath.return_value = mock_path

    write_versioned_pandas(df, "gs://bucket/folder/file.parquet", overwrite=False)

    mock_to_parquet.assert_called_once_with("gs://bucket/folder/file.parquet")
    mock_path.fs.copy.assert_not_called()
    mock_path.fs.rm_file.assert_not_called()


@patch("src.ssb_befolkning_fagfunksjoner.versions.get_fileversions")
@patch("src.ssb_befolkning_fagfunksjoner.versions.get_next_version_number")
@patch("src.ssb_befolkning_fagfunksjoner.versions.UPath")
@patch("pandas.DataFrame.to_parquet")
def test_write_versioned_pandas_multiple_existing_versions(
    mock_to_parquet,
    mock_upath,
    mock_get_next_version_number,
    mock_get_fileversions,
):
    from src.ssb_befolkning_fagfunksjoner.versions import write_versioned_pandas
    import pandas as pd

    mock_get_fileversions.return_value = [
        "gs://bucket/folder/file.parquet",
        "gs://bucket/folder/file_v1.parquet",
        "gs://bucket/folder/file_v2.parquet",
    ]
    mock_get_next_version_number.return_value = 3
    df = pd.DataFrame({"col1": [1, 2, 3]})

    mock_path = MagicMock()
    mock_path.stem = "file"
    mock_path.suffix = ".parquet"
    mock_path.name = "file.parquet"
    mock_path.parent.__truediv__.side_effect = lambda x: f"gs://bucket/folder/{x}"
    mock_path.fs.copy = MagicMock()
    mock_path.fs.rm_file = MagicMock()
    mock_upath.return_value = mock_path

    write_versioned_pandas(df, "gs://bucket/folder/file.parquet", overwrite=False)

    mock_to_parquet.assert_any_call("gs://bucket/folder/file_v3.parquet")
    mock_to_parquet.assert_any_call("gs://bucket/folder/file.parquet")
    mock_path.fs.copy.assert_not_called()
    mock_path.fs.rm_file.assert_not_called()
