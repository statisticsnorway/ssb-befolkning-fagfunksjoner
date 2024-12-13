"""This module contains functions for versioning data in GCS.

The purpose of the module in parallell to the Fagfunksjoner.versions module is to fill some of its shortcomings.
Namely, the versioning from Fagfunksjoner does not handle files without versioning. We want to keep the newest file 
unversioned in GCS. 

This versioning module also includes the function write_versioned_pandas() which acts as dp.write_pandas(), but means that
files get version numbers according to the SSB standard (with one file unversioned) and the user of the function never has to 
consider version numbers. 
"""

import dapla as dp
import pandas as pd
from dapla import FileClient
from pathlib import Path
import logging

fs = dp.FileClient.get_gcs_file_system()


def deconstruct_file_pattern(filepath: str) -> str:
    path: Path = Path(filepath)
    stem: str = path.stem
    folders: Path = path.parent
    stem_without_version: str = stem.split(sep="_v")[
        0
    ]  # if no versioning on filename, then still returns stem_without_version

    return f"{str(folders)}/{stem_without_version}*.parquet"


def get_fileversions(filepath: str) -> list[str]:

    glob_pattern: str = deconstruct_file_pattern(filepath=filepath)
    fs = FileClient.get_gcs_file_system()

    files_list: list[str] = fs.glob(path=glob_pattern)

    return files_list


def get_version_number_from_filepath(filepath: str) -> int | None:
    path: Path = Path(filepath)
    stem: str = path.stem

    occurrences: int = stem.count("_v")
    if occurrences > 1:
        raise ValueError(
            f"Multiple '_v' occurrences found in '{stem}'. Filename does not follow the expected convention."
        )

    if occurrences == 1:
        return int(stem.split(sep="_v", maxsplit=1)[1])
    else:
        return None


def get_latest_version_number(filepath: str) -> int:

    files_list: list[str] = get_fileversions(filepath)

    if not files_list:
        return 0

    version_numbers: list[int | None] = [
        get_version_number_from_filepath(filepath=fp) for fp in files_list
    ]
    numeric_versions: list[int] = [(v if v is not None else 1) for v in version_numbers]
    return max(numeric_versions)


def get_next_version_number(filepath: str) -> int:
    """
    Determine the next version number for a given file according to SSB versioning conventions.

    If the file already has versioned filenames available (e.g., '_v1', '_v2', etc.),
    it returns one greater than the latest existing version. If no versioned files exist yet,
    it defaults to 1.
    """
    latest_version_number: int = get_latest_version_number(filepath=filepath)

    return latest_version_number + 1


def validate_file_naming(filepath: str) -> None:
    """
    Validate that the file follows the expected naming convention.
    Raises ValueError if the naming is invalid.
    """
    path = Path(filepath)
    stem = path.stem
    if "_v" in stem and not stem.split("_v")[-1].isdigit():
        raise ValueError(f"File {filepath} does not follow expected naming convention.")


def write_versioned_pandas(
    df: pd.DataFrame, gcs_path: str, overwrite: bool = False
) -> None:
    """
    Write a pandas DataFrame as a Parquet file to a given GCS path, managing versions

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

    path: Path = Path(gcs_path)
    folders: Path = path.parent
    stem: str = path.stem
    stem_without_version: str = stem.split(sep="_v")[0]

    if stem != stem_without_version and not overwrite:
        raise ValueError(
            "Detected versioning in function parameter: gcs_path. "
            "For overwrite=False make sure filename does not contain version suffix. "
            "Use the basename and the function will handle versioning. "
        )

    # Find next version number
    next_version_number: int = get_next_version_number(filepath=gcs_path)

    # Log the list of files in the directory
    logging.info(f"Files in path for {gcs_path}: {get_fileversions(filepath=gcs_path)}")

    # Handle overwrite case
    if overwrite:
        try:
            dp.write_pandas(df=df, gcs_path=gcs_path)
        except Exception as e:
            logging.error(f"Failed to overwrite data at {gcs_path}: {e}")
            raise
        logging.info(f"Overwrote data: {stem}")
        return

    # Handle none-overwrite case
    if next_version_number == 2:
        # Rename existing unversioned file to v1
        old_path: Path = folders / f"{stem_without_version}.parquet"
        new_path_v1: Path = folders / f"{stem_without_version}_v1.parquet"
        try:
            fs.mv(str(old_path), str(new_path_v1))
        except Exception as e:
            logging.error(f"Failed to rename {old_path} to {new_path_v1}: {e}")
            raise
        logging.info(f"Renamed {old_path} to {new_path_v1}")

        # Write new file as v2
        new_path_v2: Path = folders / f"{stem_without_version}_v2.parquet"
        try:
            dp.write_pandas(df=df, gcs_path=str(new_path_v2))
        except Exception as e:
            logging.error(f"Failed to write version: {new_path_v2}: {e}")
            raise
        logging.info(f"Wrote new version: {new_path_v2}")

    elif next_version_number > 2:
        # Write the next version v{n}
        new_path_vn: Path = (
            folders / f"{stem_without_version}_v{next_version_number}.parquet"
        )
        try:
            dp.write_pandas(df=df, gcs_path=str(new_path_vn))
        except Exception as e:
            logging.error(f"Failed to write version: {new_path_vn}: {e}")
        logging.info(f"Wrote new version: {new_path_vn}")

    # Update the unversioned file to reflect the latest data
    latest_version_path: Path = folders / f"{stem_without_version}.parquet"
    try:
        dp.write_pandas(df=df, gcs_path=str(latest_version_path))
    except Exception as e:
        logging.error(f"Failed to update latest version: {latest_version_path}: {e}")
        raise
    logging.info(f"Updated latest version: {latest_version_path}")
