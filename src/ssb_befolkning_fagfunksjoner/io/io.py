from collections.abc import Sequence
from pathlib import Path
from typing import Any
from typing import cast

import pandas as pd
import polars as pl
from upath import UPath


def _resolve_case_indep_cols(
    available_cols: Sequence[str], requested_cols: Sequence[str]
) -> list[str]:
    """Map requested column names case-independently to actual column names."""
    col_mapping = {col.lower(): col for col in available_cols}

    missing = [col for col in requested_cols if col.lower() not in col_mapping]
    if missing:
        raise ValueError(f"Cannot find columns: {missing}")

    return [col_mapping[c.lower()] for c in requested_cols]


def read_csv_case_indep_pl(
    filepath: str | Path | UPath, cols: list[str] | None = None, **kwargs: Any
) -> pl.DataFrame:
    """Read a CSV file using Polars with case-insensitive column selection.

    Args:
        filepath: Path to the CSV file.
        cols: Optional list of columns to select, ignoring case.
        **kwargs: Additional keyword arguments passed to polars.read_csv.

    Returns:
        pl.DataFrame: DataFrame with lowercase column names.
    """
    filepath_str = str(filepath)

    if cols is not None:
        colnames = pl.read_csv(filepath_str, n_rows=0, **kwargs).collect_schema().names()
        cols = _resolve_case_indep_cols(colnames, cols)

    df = pl.read_csv(filepath_str, columns=cols, **kwargs)
    return df.rename({c: c.lower() for c in df.columns})


def read_csv_case_indep_pd(
    filepath: str | Path | UPath, cols: list[str] | None = None, **kwargs: Any
) -> pd.DataFrame:
    """Read a CSV file using pandas with case-insensitive column selection.

    Args:
        filepath: Path to the CSV file.
        cols: Optional list of columns to select, ignoring case.
        **kwargs: Additional keyword arguments passed to pandas.read_csv.

    Returns:
        pd.DataFrame: DataFrame with lowercase column names.
    """
    filepath_str = str(filepath)

    if cols is not None:
        colnames = pd.read_csv(filepath_str, nrows=0, **kwargs).columns.tolist()
        cols = _resolve_case_indep_cols(colnames, cols)

    df = pd.read_csv(filepath_str, usecols=cols, **kwargs)
    df.columns = df.columns.str.lower()
    return cast(pd.DataFrame, df)
