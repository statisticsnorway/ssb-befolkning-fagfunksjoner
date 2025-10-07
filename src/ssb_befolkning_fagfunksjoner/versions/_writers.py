import logging

import pandas as pd
from upath import UPath


def promote_unversioned_to_v1(parent: UPath, stem: str) -> None:
    old_path: UPath = parent / f"{stem}.parquet"
    new_path: UPath = parent / f"{stem}_v1.parquet"
    try:
        logging.info(f"Renaming {old_path} to {new_path}")
        old_path.rename(target=new_path)
    except Exception as e:
        logging.error(f"Failed to rename {old_path} to {new_path}: {e}")
        raise


def write_new_version(
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


def update_latest_file(df: pd.DataFrame, parent: UPath, stem: str) -> None:
    latest_path = parent / f"{stem}.parquet"
    try:
        logging.info(f"Updating latest version: {latest_path}")
        df.to_parquet(latest_path)
        logging.info("Success!")
    except Exception as e:
        logging.error(f"Failed to update latest version: {latest_path}: {e}")
        raise
