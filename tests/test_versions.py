from ssb_befolkning_fagfunksjoner.versions import write_versioned_pandas

def test_deconstruct_file_pattern():
    from src.ssb_befolkning_fagfunksjoner.versions import deconstruct_file_pattern

    filepath = "gs://bucket/folder/file_v1.parquet"
    expected = "gs://bucket/folder/file*.parquet"
    result = deconstruct_file_pattern(filepath)
    assert result == expected

def test_get_version_number_from_filepath():
    from src.ssb_befolkning_fagfunksjoner.versions import get_version_number_from_filepath

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
        assert str(e) == "Multiple '_v' occurrences found in 'file_v2_v3'. Filename does not follow the expected convention."


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