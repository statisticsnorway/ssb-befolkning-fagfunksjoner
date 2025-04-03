"""This module contains functions for versioning data in GCS.

The purpose of the module in parallell to the `Fagfunksjoner.versions` module is to fill some of its shortcomings.
Namely, the versioning from Fagfunksjoner does not handle files without versioning. We want to keep the newest file
unversioned in GCS.

This versioning module also includes the function write_versioned_pandas() which acts as dp.write_pandas(), but means that
files get version numbers according to the SSB standard (with one file unversioned) and the user of the function never has to
consider version numbers.
"""

import logging
from typing import cast

import pandas as pd
from fsspec.spec import AbstractFileSystem  # type: ignore
from upath import UPath


def deconstruct_file_pattern(filepath: str) -> str:
    """Returns a glob pattern (string) with folders and base filename without specifying version."""
    path = UPath(filepath, protocol="gs")
    stem: str = path.stem
    parent = path.parent
    stem_without_version: str = stem.rpartition("_v")[
        0
    ]  # if no versioning on filename, then still returns stem_without_version

    return f"{parent!s}/{stem_without_version}*.parquet"


def get_fileversions(filepath: str) -> list[str]:
    """Returns a list of versioned files in gcs filepath."""
    glob_pattern: str = deconstruct_file_pattern(filepath)
    path = UPath(filepath, protocol="gs")
    fs: AbstractFileSystem = path.fs

    try:
        files_list: list[str] = cast(list[str], fs.glob(glob_pattern))
    except Exception as e:
        raise RuntimeError(f"Failed to glob files with pattern '{glob_pattern}'") from e

    return files_list


def get_version_number_from_filepath(filepath: str) -> int | None:
    """Returns the version number from a gcs filepath including versioned filename."""
    path = UPath(filepath, protocol="gs")
    stem: str = path.stem
    _, sep, suffix = stem.rpartition("_v")

    if not sep or not suffix.isdigit():
        logging.warning(f"No valid version number found in {stem}.")
        return None
    return int(suffix)


def get_latest_version_number(filepath: str) -> int:
    """Return the latest version number for the files in a given gcs filepath."""
    files_list: list[str] = get_fileversions(filepath)

    if not files_list:
        return 0

    version_numbers: list[int | None] = [
        get_version_number_from_filepath(filepath=fp) for fp in files_list
    ]
    numeric_versions: list[int] = [(v if v is not None else 1) for v in version_numbers]
    return max(numeric_versions)


def get_next_version_number(filepath: str) -> int:
    """Determine the next version number for a given file according to SSB versioning conventions.

    If the file already has versioned filenames available (e.g., '_v1', '_v2', etc.),
    it returns one greater than the latest existing version. If no versioned files exist yet,
    it defaults to 1.
    """
    latest_version_number: int = get_latest_version_number(filepath=filepath)

    return latest_version_number + 1


def validate_file_naming(filepath: str) -> None:
    """Validate that the file follows the expected naming convention.

    Raises ValueError if the naming is invalid.
    """
    path = UPath(filepath, protocol="gs")
    stem: str = path.stem
    if "_v" in stem and not stem.split("_v")[-1].isdigit():
        raise ValueError(f"File {filepath} does not follow expected naming convention.")


def write_versioned_pandas(
    df: pd.DataFrame, gcs_path: str, overwrite: bool = False
) -> None:
    """Write a pandas DataFrame as a Parquet file to a given GCS path, managing versions.

    If `overwrite` is False, versioning behavior is as follows:
    - The first write (version_number == 1) creates a file named `<base_filename>.parquet`.
    - The second write (version_number == 2) renames the existing `<base_filename>.parquet`
      to `<base_filename>_v1.parquet` and writes the new file as `<base_filename>_v2.parquet`.
    - Subsequent writes (version_number > 2) append a new file `<base_filename>_v{n}.parquet`.
    - The newest file is always accessible as `<base_filename>.parquet`.

    If `overwrite` is True, the latest version `<base_filename>.parquet` is simply overwritten.
    """
    # Validate the naming convention
    validate_file_naming(gcs_path)

    path = UPath(gcs_path, protocol="gs")
    fs = path.fs
    parent = path.parent
    stem: str = path.stem
    stem_without_version: str = stem.split(sep="_v")[0]

    if overwrite:  # Case when overwriting data, no versioning
        df.to_parquet(gcs_path)
        logging.info(f"Overwrote data: {stem}")
        return

    if stem != stem_without_version:  # Case when input filepath has version number
        raise ValueError(
            "Detected versioning in function parameter: gcs_path. "
            "For overwrite=False make sure filename does not contain version suffix. "
            "Use the basename and the function will handle versioning. "
        )

    # Find next version number
    next_version_number: int = get_next_version_number(filepath=gcs_path)
    logging.info(f"Files in path for {gcs_path}: {get_fileversions(filepath=gcs_path)}")

    if next_version_number == 2:
        _promote_unversioned_to_v1(fs, parent, stem_without_version)
        _write_new_version(
            df, parent, stem_without_version, version=next_version_number
        )
    elif next_version_number > 2:
        _write_new_version(
            df, parent, stem_without_version, version=next_version_number
        )

    _update_latest_file(df, parent, stem_without_version)


# ---------------------------------------------------------
# Helper functions
# ---------------------------------------------------------


def _promote_unversioned_to_v1(
    fs: AbstractFileSystem, parent: UPath, stem: str
) -> None:
    old_path = parent / f"{stem}.parquet"
    new_path = parent / f"{stem}_v1.parquet"
    try:
        fs.copy(str(old_path), str(new_path))
        fs.rm_file(str(old_path))
        logging.info(f"Renamed {old_path} to {new_path}")
    except Exception as e:
        logging.error(f"Failed to rename {old_path} to {new_path}: {e}")
        raise


def _write_new_version(
    df: pd.DataFrame, parent: UPath, stem: str, version: int
) -> None:
    versioned_path = parent / f"{stem}_v{version}.parquet"
    try:
        df.to_parquet(str(versioned_path))
        logging.info(f"Wrote new version: {versioned_path}")
    except Exception as e:
        logging.error(f"Failed to write versioned DataFrame: {versioned_path}: {e}")
        raise


def _update_latest_file(df: pd.DataFrame, parent: UPath, stem: str) -> None:
    latest_path = parent / f"{stem}.parquet"
    try:
        df.to_parquet(str(latest_path))
        logging.info(f"Updated latest version: {latest_path}")
    except Exception as e:
        logging.error(f"Failed to update latest version: {latest_path}: {e}")
        raise
