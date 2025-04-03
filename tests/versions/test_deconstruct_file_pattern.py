from ssb_befolkning_fagfunksjoner.versions import deconstruct_file_pattern
import pytest

@pytest.mark.parametrize(
    "input_path, expected_pattern",
    [
        ("gs://bucket/folder/file_v1.parquet", "gs://bucket/folder/file*.parquet"),
        ("bucket/folder/file_v2.parquet", "gs://bucket/folder/file*.parquet"),
        ("gs://bucket/folder_with_underscore/file_v3.parquet", "gs://bucket/folder_with_underscore/file*.parquet"),
    ]
)
def test_deconstruct_file_pattern(input_path: str, expected_pattern: str) -> None:
    result = deconstruct_file_pattern(input_path)
    assert result == expected_pattern
