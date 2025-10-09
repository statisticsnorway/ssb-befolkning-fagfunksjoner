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
    normalised: UPath = resolve_path(filepath)
    parent: UPath = normalised.parent
    stem: str = normalised.stem

    if re.search(r"_v\d+$", stem):  # Case when input filepath has version number
        raise ValueError(
            "Detected versioning in function parameter: `filepath` "
            "Use the basename (without version suffix) and the function will handle versioning. "
        )

    latest_path: UPath = parent / f"{stem}.parquet"
    next_version_number = get_next_version_number(filepath=normalised)

    # --- CASE 1: First write to directory ---
    if next_version_number == 1:
        logging.info("No existing versions found; writing latest only.")
        update_latest_file(df=df, parent=parent, stem=stem)
        return

    latest_exists: bool = latest_path.exists()
    
    if next_version_number == 2 and not latest_exists:
        raise ValueError(f"Expected '{latest_path}' to exist, but was not found.")

    # Compare df to existing file
    if latest_exists:
        try:
            existing_df = pd.read_parquet(latest_path)
        except Exception as e:
            raise ValueError(f"Failed to read existing version at '{latest_path}'") from e

        if existing_df.equals(df):
            logging.info("No changes detected; skipping write.")
            return

    # --- CASE 2: Writing versioned file ---
    if next_version_number == 2:
        promote_unversioned_to_v1(parent=parent, stem=stem)

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
