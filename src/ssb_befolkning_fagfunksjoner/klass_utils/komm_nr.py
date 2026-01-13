import datetime
import logging
import warnings
from typing import Any

import klass
import pandas as pd
from tabulate import tabulate

from ..klass_utils.change_mapping import get_klass_change_mapping

logger = logging.getLogger(__name__)


__all__ = ["get_komm_nr_changes", "update_komm_nr", "validate_komm_nr"]


# ------------------------------------------------------------------------
# Validation
# ------------------------------------------------------------------------


def _load_komm_nr(year: int | str) -> dict[str, str]:
    """Load KLASS codelist for municipalities."""
    kommune_dict: dict[str, str] = (
        klass.KlassClassification(131).get_codes(from_date=f"{year}-01-02").to_dict()
    )

    # Handle missing values
    kommune_dict.pop("9999", None)
    kommune_dict["0000"] = "Sperret adresse"

    return kommune_dict


def validate_komm_nr(codes: pd.Series, year: int | str) -> None:
    """Validate that all codes exist in the KLASS codelist for the given year."""
    valid_codes = set(_load_komm_nr(year).keys())
    invalid_codes = set(codes) - valid_codes

    if invalid_codes:
        raise ValueError(f"Invalid municipality codes found: {sorted(invalid_codes)}")
    else:
        logger.info("All municipality codes align with KLASS data.")


# ------------------------------------------------------------------------
# Update komm_nr
# ------------------------------------------------------------------------


def _get_latest_komm_nr(code: str, komm_nr_change_dict: dict[str, str]) -> str:
    """Recursively find the latest municipality code using a dict of municipality code changes."""
    start_code = code
    seen: set[Any] = set()

    while code in komm_nr_change_dict:
        if code in seen:
            raise ValueError(
                "Found a cycle of municipality codes. "
                f"{start_code}. Revisited code: {code}. Seen: {sorted(seen)}"
            )

        seen.add(code)
        code = komm_nr_change_dict[code]

    return code


def _log_municipality_update(original: pd.Series, updated: pd.Series) -> None:
    """Log how many codes were updated and show distribution table."""
    changes_mask = original.ne(updated)
    updated_count = changes_mask.sum()
    logger.info(f"{updated_count} municipality codes were updated.")

    if updated_count == 0:
        return

    update_distr = (
        pd.DataFrame(
            {
                "from": original[changes_mask],
                "to": updated[changes_mask],
            }
        )
        .value_counts()
        .reset_index(name="count")
        .sort_values("count", ascending=False)
    )

    table_str = tabulate(
        update_distr.to_records(index=False),
        headers="keys",
        tablefmt="pretty",
        showindex=False,
    )

    logger.info("Distribution of municipality code updates:\n" + table_str)


def update_komm_nr(
    original_codes: pd.Series,
    year: int | str,
    validate: bool = True,
) -> pd.Series:
    """Update municipality codes based on KLASS change tables.

    This function:
    - Applies recursive updates from the old_code → new_code mappings until the latest code is reached.
    - Replaces missing values with '0000' and logs their count.
    - Logs the number of updated municipality codes and a distribution table.
    - Checks for municipality splits and logs warnings if any are found.
    - Validates that all updated codes exist in the official KLASS list for the given year.

    Parameters:
        original_codes: pd.Series
            A pandas Series containing the original municipality codes.
        year: int | str
            The year for which to apply the KLASS mappings.
        validate: bool
            Boolean flag which determines whether to run validation or not (default = True).

    Returns:
        pd.Series[str]
            A pandas Series containing the updated municipality codes.
    """
    komm_nr_changes, komm_nr_splits = get_komm_nr_changes(
        target_date=datetime.date(int(year), 1, 1)
    )
    komm_nr_changes_dict = komm_nr_changes.set_index("old_code").to_dict()["new_code"]

    original_codes = original_codes.fillna("0000")
    logger.info(
        f"{len(original_codes[original_codes == '0000'])} rows where municipality code = '0000'"
    )

    updated_codes = original_codes.map(
        lambda code: _get_latest_komm_nr(code, komm_nr_changes_dict)
    )

    _log_municipality_update(original_codes, updated_codes)

    split_codes = set(updated_codes).intersection(set(komm_nr_splits["old_code"]))
    if split_codes:
        warnings.warn(
            f"Municipality splits detected for codes: {komm_nr_splits[komm_nr_splits['old_code'].isin(split_codes)]}",
            stacklevel=2,
        )

    # Verify municipality codes against KLASS
    if validate:
        validate_komm_nr(updated_codes, year)

    return updated_codes


# ------------------------------------------------------------------------
# Get komm_nr changes
# ------------------------------------------------------------------------


def get_komm_nr_changes(
    from_date: str | datetime.date = datetime.date(1980, 1, 1),
    to_date: str | datetime.date | None = None,
    target_date: str | datetime.date | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load municipality code (komm_nr) changes from KLASS.

    Parameters:
        from_date: str | datetime.date
            Lower bound date for change history to include. Defaults to 1980-01-01.
        to_date: str | datetime.date | None
            Upper bound date for change history to include. Defaults to today.
        target_date: str | datetime.date | None
            Target date for municipality code mappings. Defaults to today.

    Returns:
        tuple[pd.DataFrame, pd.DataFrame]
            A tuple ``(changes, splits)`` with mappings from `old_code` to `new_code`.
            Split into codes that map to exactly one new code, and codes that map to multiple new codes.

    Raises:
        ValueError: If any of the input parameters are not the correct type.
    """
    # Input validation
    for name, val in {
        "from_date": from_date,
        "to_date": to_date,
        "target_date": target_date,
    }.items():
        if val is not None and not isinstance(val, (str, datetime.date)):
            raise ValueError(
                f"Invalid type for {name}: {type(val).__name__}. Expected str or datetime.date."
            )

    # Normalise date-input
    if isinstance(to_date, str):
        to_date = datetime.date.fromisoformat(to_date)
    if isinstance(from_date, str):
        from_date = datetime.date.fromisoformat(from_date)
    if isinstance(target_date, str):
        target_date = datetime.date.fromisoformat(target_date)
    if target_date is None and to_date is not None:
        target_date = to_date

    komm_nr_classification: klass.KlassClassification = klass.KlassClassification(131)

    # Read Series mapping old_code (index) -> new_code (value)
    komm_nr_change_series = get_klass_change_mapping(
        komm_nr_classification,
        target_date=target_date,
        to_date=to_date,
        from_date=from_date,
    )

    # Drop non-changes
    komm_nr_change_series = komm_nr_change_series.loc[
        komm_nr_change_series.index != komm_nr_change_series
    ]

    # Identify splits and drop them from `changes`
    is_split = komm_nr_change_series.index.duplicated(keep=False)

    def _as_df(s: pd.Series) -> pd.DataFrame:
        df = s.rename("new_code").reset_index()
        df = df.rename(columns={"index": "old_code"})
        return df

    komm_nr_splits: pd.DataFrame = _as_df(komm_nr_change_series[is_split])
    komm_nr_changes: pd.DataFrame = _as_df(komm_nr_change_series[~is_split])

    return komm_nr_changes, komm_nr_splits
