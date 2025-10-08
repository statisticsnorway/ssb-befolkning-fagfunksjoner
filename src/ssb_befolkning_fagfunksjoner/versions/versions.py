import logging
import re

import pandas as pd
from upath import UPath

from ._numbering import get_latest_version_number
from ._path import resolve_path
from ._writers import promote_unversioned_to_v1, create_versioned_file, update_latest_file

__all__ = ["write_versioned_pandas", "get_next_version_number"]


def write_versioned_pandas(
    df: pd.DataFrame,
    filepath: str | UPath,
) -> None:
    """Write a pandas DataFrame as a Parquet file to a given GCS path, managing versions.

    Versioning behavior is as follows:
    - The first write (version_number == 1) creates a file named `<base_filename>.parquet`.
    - The second write (version_number == 2) renames the existing `<base_filename>.parquet`
      to `<base_filename>_v1.parquet` and writes the new file as `<base_filename>_v2.parquet`.
    - Subsequent writes (version_number > 2) append a new file `<base_filename>_v{n}.parquet`.

    - The newest file is always accessible as `<base_filename>.parquet`.
    """
    normalised_filepath: UPath = resolve_path(filepath)
    parent: UPath = normalised_filepath.parent
    stem: str = normalised_filepath.stem

    if re.search(r"_v\d+$", stem):  # Case when input filepath has version number
        raise ValueError(
            "Detected versioning in function parameter: `filepath` "
            "Use the basename (without version suffix) and the function will handle versioning. "
        )

    next_version_number = get_next_version_number(
        filepath=normalised_filepath
    )
    latest_path: UPath = parent / f"{stem}.parquet"

    # --- CASE 1: First write to directory ---
    if next_version_number == 1:
        logging.info("No existing versions of DataFrame found.")
        update_latest_file(df=df, parent=parent, stem=stem)
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
        promote_unversioned_to_v1(parent=parent, stem=stem)

    versioned_path: UPath = parent / f"{stem}_v{next_version_number}.parquet"
    logging.info(f"Detected change — writing version {next_version_number} to {versioned_path}")
    create_versioned_file(df=df, parent=parent, stem=stem, version=next_version_number)
    update_latest_file(df=df, parent=parent, stem=stem)


def get_next_version_number(filepath: str | UPath) -> int:
    """Determine the next version number for a given file according to SSB versioning conventions.

    If the file already has versioned filenames available (e.g., '_v1', '_v2', etc.),
    it returns one greater than the latest existing version. If no versioned files exist yet,
    it defaults to 1.
    """
    normalised_filepath: UPath = resolve_path(filepath)
    latest_version_number = get_latest_version_number(filepath=normalised_filepath)

    return latest_version_number + 1
