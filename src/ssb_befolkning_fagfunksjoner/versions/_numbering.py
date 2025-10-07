"""This module contains internal functions for versioning data in GCS."""

import logging
import re

from upath import UPath


def get_glob_pattern(filepath: UPath) -> str:
    """Returns a glob pattern (string) with base filename without specified version."""
    stem = filepath.stem
    stem_without_version = re.sub(r"_v\d+$", "", stem)
    return f"{stem_without_version}*.parquet"


def get_list_of_versioned_files(filepath: UPath) -> list[UPath]:
    """Returns a list of versioned files in gcs filepath."""
    glob_pattern: str = get_glob_pattern(filepath)
    parent = filepath.parent

    try:
        files_list: list[UPath] = list(parent.glob(glob_pattern))
        return files_list
    except Exception as e:
        raise RuntimeError(f"Failed to glob files with pattern '{glob_pattern}'") from e


def get_version_number_from_filepath(filepath: UPath) -> int | None:
    """Extracts the version number from a filename with a `_v<digit>` suffix, or returns None if not present."""
    match = re.search(r"_v(\d+)$", filepath.stem)
    if not match:
        logging.warning(f"No valid version number found in {filepath.stem}.")
        return None
    return int(match.group(1))


def get_latest_version_number(filepath: UPath) -> int:
    """Return the latest version number for the files in a given gcs filepath."""
    files_list: list[UPath] = get_list_of_versioned_files(filepath)

    if not files_list:
        return 0

    version_numbers: list[int | None] = [
        get_version_number_from_filepath(filepath=fp) for fp in files_list
    ]
    numeric_versions: list[int] = [(v if v is not None else 1) for v in version_numbers]
    return max(numeric_versions)


def get_next_version_number(filepath: UPath) -> int:
    """Determine the next version number for a given file according to SSB versioning conventions.

    If the file already has versioned filenames available (e.g., '_v1', '_v2', etc.),
    it returns one greater than the latest existing version. If no versioned files exist yet,
    it defaults to 1.
    """
    latest_version_number: int = get_latest_version_number(filepath=filepath)

    return latest_version_number + 1
