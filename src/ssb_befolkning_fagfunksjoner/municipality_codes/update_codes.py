"""This module contains functions for updating municipality codes using KLASS codelists."""

import logging

import pandas as pd

from ..klass_utils.loaders import load_kommnr_changes
from ._logging_utils import log_municipality_update
from .validation import validate_municipality_codes

logger = logging.getLogger(name=__name__)


def update_municipality_codes(
    original_codes: pd.Series,
    year: int,
) -> pd.Series:
    """Update municipality codes based on KLASS change tables.

    This function:
    - Applies recursive updates from the oldCode → newCode mappings until the latest code is reached.
    - Replaces missing values with '0000' and logs their count.
    - Logs the number of updated municipality codes and a distribution table.
    - Checks for municipality splits and logs warnings if any are found.
    - Validates that all updated codes exist in the official KLASS list for the given year.

    Args:
        original_codes (pd.Series[str]): A pandas Series containing the original municipality codes.
        year (int): The year for which to apply the KLASS mappings.

    Returns:
        pd.Series[str]: A pandas Series containing the updated municipality codes.
    """
    kommnr_changes, kommnr_splits = load_kommnr_changes(to_date=f"{year}-01-02")
    kommnr_changes_dict = kommnr_changes.set_index("oldCode").to_dict()["newCode"]

    original_codes = original_codes.fillna("0000")
    logger.info(
        f"{len(original_codes[original_codes == '0000'])} rows where municipality code = '0000'"
    )

    updated_codes = original_codes.map(
        lambda code: _get_latest_municipality_code(code, kommnr_changes_dict)
    )

    log_municipality_update(original_codes, updated_codes)

    split_codes = set(updated_codes).intersection(set(kommnr_splits["oldCode"]))
    if split_codes:
        logger.warning(f"Municipality splits detected for codes: {sorted(split_codes)}")

    # Verify municipality codes against KLASS
    validate_municipality_codes(updated_codes, year)

    return updated_codes


# ---------------------------------------------------------
# Helper functions
# ---------------------------------------------------------


def _get_latest_municipality_code(code: str, kommnr_change_dict: dict[str, str]) -> str:
    """Recursively find the latest municipality code using the kommnr_change_dict."""
    # Traverse the dictionary to find the latest code after all updates
    try:
        while code in kommnr_change_dict.keys():
            code = kommnr_change_dict[code]
        return code
    except Exception as e:
        logger.error(f"Error finding latest code for {code}: {e}")
        raise e
