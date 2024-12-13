@patch("src.ssb_befolkning_fagfunksjoner.versions.dp.write_pandas")
@patch("src.ssb_befolkning_fagfunksjoner.versions.fs.mv")
@patch("src.ssb_befolkning_fagfunksjoner.versions.get_next_version_number")
@patch("src.ssb_befolkning_fagfunksjoner.versions.get_fileversions")
def test_write_versioned_pandas(mock_get_fileversions, mock_get_next_version_number, mock_fs_mv, mock_write_pandas):
    from src.ssb_befolkning_fagfunksjoner.versions import write_versioned_pandas

    # Mock return values
    mock_get_fileversions.return_value = ["gs://bucket/folder/file.parquet"]
    mock_get_next_version_number.return_value = 2

    # Create a dummy DataFrame
    import pandas as pd
    df = pd.DataFrame({"col1": [1, 2, 3]})

    # Call the function
    write_versioned_pandas(df, "gs://bucket/folder/file.parquet", overwrite=False)

    # Assert write_pandas was called for version 2 and unversioned file
    mock_write_pandas.assert_any_call(df=df, gcs_path="gs://bucket/folder/file_v2.parquet")
    mock_write_pandas.assert_any_call(df=df, gcs_path="gs://bucket/folder/file.parquet")

    # Assert mv was called for renaming unversioned to v1
    mock_fs_mv.assert_called_once_with("gs://bucket/folder/file.parquet", "gs://bucket/folder/file_v1.parquet")


from unittest.mock import patch, MagicMock


@patch("src.ssb_befolkning_fagfunksjoner.versions.dp.write_pandas")
@patch("src.ssb_befolkning_fagfunksjoner.versions.fs.mv")
@patch("src.ssb_befolkning_fagfunksjoner.versions.get_next_version_number")
@patch("src.ssb_befolkning_fagfunksjoner.versions.get_fileversions")
def test_write_versioned_pandas_no_existing_files(
    mock_get_fileversions, mock_get_next_version_number, mock_fs_mv, mock_write_pandas
):
    from src.ssb_befolkning_fagfunksjoner.versions import write_versioned_pandas

    # Mock return values
    mock_get_fileversions.return_value = []  # No existing files
    mock_get_next_version_number.return_value = 1

    # Create a dummy DataFrame
    import pandas as pd
    df = pd.DataFrame({"col1": [1, 2, 3]})

    # Call the function
    write_versioned_pandas(df, "gs://bucket/folder/file.parquet", overwrite=False)

    # Assert write_pandas was called only for the unversioned file
    mock_write_pandas.assert_called_once_with(df=df, gcs_path="gs://bucket/folder/file.parquet")

    # Assert no file renames were attempted
    mock_fs_mv.assert_not_called()


@patch("src.ssb_befolkning_fagfunksjoner.versions.dp.write_pandas")
@patch("src.ssb_befolkning_fagfunksjoner.versions.fs.mv")
@patch("src.ssb_befolkning_fagfunksjoner.versions.get_next_version_number")
@patch("src.ssb_befolkning_fagfunksjoner.versions.get_fileversions")
def test_write_versioned_pandas_several_existing_files(
    mock_get_fileversions, mock_get_next_version_number, mock_fs_mv, mock_write_pandas
):
    from src.ssb_befolkning_fagfunksjoner.versions import write_versioned_pandas

    # Mock return values
    mock_get_fileversions.return_value = [
        "gs://bucket/folder/file.parquet",
        "gs://bucket/folder/file_v1.parquet",
        "gs://bucket/folder/file_v2.parquet",
    ]  # Several existing files
    mock_get_next_version_number.return_value = 3

    # Create a dummy DataFrame
    import pandas as pd
    df = pd.DataFrame({"col1": [1, 2, 3]})

    # Call the function
    write_versioned_pandas(df, "gs://bucket/folder/file.parquet", overwrite=False)

    # Assert write_pandas was called for the next version and the unversioned file
    mock_write_pandas.assert_any_call(df=df, gcs_path="gs://bucket/folder/file_v3.parquet")
    mock_write_pandas.assert_any_call(df=df, gcs_path="gs://bucket/folder/file.parquet")

    # Assert no file renames were attempted, as unversioned was already handled previously
    mock_fs_mv.assert_not_called()

