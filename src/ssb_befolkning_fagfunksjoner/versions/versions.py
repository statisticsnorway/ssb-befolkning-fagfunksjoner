"""This module contains functions for versioning data in GCS.

The purpose of the module in parallell to the `Fagfunksjoner.versions` module is to fill some of its shortcomings.
Namely, the versioning from Fagfunksjoner does not handle files without versioning. We want to keep the newest file
unversioned in GCS.

This versioning module also includes the function write_versioned_pandas() which acts as dp.write_pandas(), but means that
files get version numbers according to the SSB standard (with one file unversioned) and the user of the function never has to
consider version numbers.
"""

import logging
import re

import pandas as pd
from upath import UPath

from . import _versions


def get_next_version_number(filepath: str) -> int:
    """Determine the next version number for a given file according to SSB versioning conventions.

    If the file already has versioned filenames available (e.g., '_v1', '_v2', etc.),
    it returns one greater than the latest existing version. If no versioned files exist yet,
    it defaults to 1.
    """
    normalised_filepath: UPath = _versions.resolve_path(filepath)
    return _versions.get_next_version_number(filepath=normalised_filepath)


def write_versioned_pandas(
    df: pd.DataFrame,
    filepath: str,
) -> None:
    """Write a pandas DataFrame as a Parquet file to a given GCS path, managing versions.

    Versioning behavior is as follows:
    - The first write (version_number == 1) creates a file named `<base_filename>.parquet`.
    - The second write (version_number == 2) renames the existing `<base_filename>.parquet`
      to `<base_filename>_v1.parquet` and writes the new file as `<base_filename>_v2.parquet`.
    - Subsequent writes (version_number > 2) append a new file `<base_filename>_v{n}.parquet`.

    - The newest file is always accessible as `<base_filename>.parquet`.
    """
    normalised_filepath: UPath = _versions.resolve_path(filepath)
    parent: UPath = normalised_filepath.parent
    stem: str = normalised_filepath.stem

    if re.search(r"_v\d+$", stem):  # Case when input filepath has version number
        raise ValueError(
            "Detected versioning in function parameter: filepath. "
            "Use the basename (without version suffix) and the function will handle versioning. "
        )

    next_version_number: int = _versions.get_next_version_number(
        filepath=normalised_filepath
    )
    latest_path: UPath = parent / f"{stem}.parquet"

    # --- CASE 1: First write to directory ---
    if next_version_number == 1:
        logging.info("No existing versions of DataFrame found.")
        _update_latest_file(df=df, parent=parent, stem=stem)
        return

    # Compare df to existing file
    if latest_path.exists():
        try:
            existing_df = pd.read_parquet(latest_path)
            if existing_df.equals(df):
                logging.info(
                    f"No changes detected in {latest_path}. Skipping write to path."
                )
                return
        except Exception as e:
            logging.error(
                f"Failed to read existing version at {latest_path} for comparison: {e}"
            )
            raise
    else:
        if next_version_number == 2:
            raise RuntimeError(
                f"Expected {latest_path} to exist for rename to _v1, but it was not found."
            )

    # --- CASE 2: Writing versioned file ---
    if next_version_number == 2:
        _promote_unversioned_to_v1(parent=parent, stem=stem)

    versioned_path: UPath = parent / f"{stem}_v{next_version_number}.parquet"
    logging.info(
        f"Detected change — writing version {next_version_number} to {versioned_path}"
    )
    _write_new_version(df=df, parent=parent, stem=stem, version=next_version_number)
    _update_latest_file(df=df, parent=parent, stem=stem)


# ---------------------------------------------------------
# Helper functions
# ---------------------------------------------------------


def _promote_unversioned_to_v1(parent: UPath, stem: str) -> None:
    old_path: UPath = parent / f"{stem}.parquet"
    new_path: UPath = parent / f"{stem}_v1.parquet"
    try:
        logging.info(f"Renaming {old_path} to {new_path}")
        old_path.rename(target=new_path)
    except Exception as e:
        logging.error(f"Failed to rename {old_path} to {new_path}: {e}")
        raise


def _write_new_version(
    df: pd.DataFrame, parent: UPath, stem: str, version: int
) -> None:
    versioned_path: UPath = parent / f"{stem}_v{version}.parquet"
    try:
        logging.info(f"Writing new version: {versioned_path}")
        df.to_parquet(versioned_path)
        logging.info("Success!")
    except Exception as e:
        logging.error(f"Failed to write versioned DataFrame: {versioned_path}: {e}")
        raise


def _update_latest_file(df: pd.DataFrame, parent: UPath, stem: str) -> None:
    latest_path = parent / f"{stem}.parquet"
    try:
        logging.info(f"Updating latest version: {latest_path}")
        df.to_parquet(latest_path)
        logging.info("Success!")
    except Exception as e:
        logging.error(f"Failed to update latest version: {latest_path}: {e}")
        raise
