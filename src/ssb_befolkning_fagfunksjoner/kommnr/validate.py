import logging

import pandas as pd
import klass

logger = logging.getLogger(name=__name__)

__all__ = ["validate_kommnr"]


def _load_kommnr(year: int | str) -> dict[str, str]:
    """Load KLASS codelist for municipalities."""
    kommune_dict: dict[str, str] = (
        klass.KlassClassification(131)
        .get_codes(from_date=f"{year}-01-01")
        .to_dict()
    )

    # Handle missing values
    kommune_dict.pop("9999", None)
    kommune_dict["0000"] = "Sperret adresse"

    return kommune_dict


def validate_kommnr(codes: pd.Series, year: int | str) -> None:
    """Validate that all codes exist in the KLASS codelist for the given year."""
    valid_codes = set(_load_kommnr(f"{year}-01-02").keys())
    invalid_codes = set(codes) - valid_codes

    if invalid_codes:
        raise ValueError(f"Invalid municipality codes found: {sorted(invalid_codes)}")
    else:
        logger.info("All municipality codes align with KLASS data.")
