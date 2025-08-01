import logging

import pandas as pd

from ..klass_utils.loaders import load_kommnr

logger = logging.getLogger(name=__name__)


def validate_municipality_codes(codes: pd.Series, year: int | str) -> None:
    """Validate that all codes exist in the KLASS codelist for the given year."""
    valid_codes = set(load_kommnr(f"{year}-01-02").keys())
    invalid_codes = set(codes) - valid_codes

    if invalid_codes:
        raise ValueError(f"Invalid municipality codes found: {sorted(invalid_codes)}")
    else:
        logger.info("All municipality codes align with KLASS data.")
