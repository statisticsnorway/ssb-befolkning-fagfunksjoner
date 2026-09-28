from pathlib import Path
from typing import Any
from typing import cast

import pandas as pd
import polars as pl
from upath import UPath


def read_csv_case_indep_pl(filepath: str | Path | UPath, cols: list[str] | None = None, **kwargs: Any) -> pl.DataFrame:
    """Reads a CSV-file using polars.read_csv choosing columns independent of upper/lower case.

    Args:
        filepath: Filepath to read from.
        cols: Optional list of columns to select.
        **kwargs: Additional arguments that get sent to polars.read_csv

    Returns:
        pl.DataFrame: Dataset with lower-case column names.
    """
    if cols is not None:
        # Read colnames and create a mapping 'lower case -> original case'
        colnames = pl.scan_csv(cast(Path, filepath), separator=";").collect_schema().names()
        col_mapping = {col.lower(): col for col in colnames}

        # Check for missing cols
        missing = [col for col in cols if col.lower() not in col_mapping]
        if missing:
            raise ValueError(f"Cannot find columns: {missing}")

        # Map selected columns to original case
        cols = [col_mapping[c.lower()] for c in cols]

    # Read dataset and lower case columns
    df = pl.read_csv(
        cast(Path, filepath),
        columns=cols,
        **kwargs,
    )
    df = df.rename({c: c.lower() for c in df.columns})

    return df


def read_csv_case_indep_pd(filepath: str | Path | UPath, cols: list[str] | None = None, **kwargs: Any) -> pd.DataFrame:
    """Reads a CSV-file using pandas.read_csv choosing columns independent of upper/lower case.

    Args:
        filepath: Filepath to read from.
        cols: Optional list of columns to select.
        **kwargs: Additional arguments that get sent to pandas.read_csv

    Returns:
        pd.DataFrame: Dataset with lower-case column names.
    """
    if cols is not None:
        # Read colnames and create a mapping 'lower case -> original case'
        colnames = pd.read_csv(cast(Path, filepath), nrows=0, **kwargs).columns.tolist()
        col_mapping = {col.lower(): col for col in colnames}

        # Check for missing cols
        missing = [col for col in cols if col.lower() not in col_mapping]
        if missing:
            raise ValueError(f"Cannot find columns: {missing}")

        # Map selected columns to original case
        cols = [col_mapping[c.lower()] for c in cols]

    # Read dataset and lower case columns
    df = cast(
        pd.DataFrame,
        pd.read_csv(
            cast(Path, filepath),
            usecols=cols,
            **kwargs,
        ))
    df.columns = df.columns.str.lower()

    return df
