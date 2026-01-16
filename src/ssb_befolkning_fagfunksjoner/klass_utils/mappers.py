from collections.abc import Hashable
from collections.abc import Sequence

import klass
import pandas as pd

__all__ = ["map_to_country_codes"]


def _load_country_codes() -> dict[str, str]:
    """Load KLASS correspondence table for country codes."""
    landkoder_dict: dict[str, str | None] = klass.KlassCorrespondence(953).to_dict()

    landkoder_dict["ANT"] = "656"
    landkoder_dict["CSK"] = "142"
    landkoder_dict["DDR"] = "151"
    landkoder_dict["PCZ"] = "669"
    landkoder_dict["SCG"] = "125"
    landkoder_dict["SKM"] = "546"
    landkoder_dict["SUN"] = "135"
    landkoder_dict["YUG"] = "125"
    landkoder_dict["XXA"] = "990"

    return {key: value for key, value in landkoder_dict.items() if value is not None}


def map_to_country_codes(
    alpha_3_col: pd.Series[str | list[str]],
) -> pd.Series[str | list[str]]:
    """Convert a Series of ISO alpha-3 codes to SSB-3 codes.

    Parameters:
        alpha_3_col: pd.Series[str | list[str]]
            A pandas series of citizenships that may contain scalars (e.g., "NOR") or sequences (e.g., ["NOR", "SWE"]).

    Returns:
        pd.Series[str | list[str]]
    """
    mapping: dict[str, str] = _load_country_codes()

    def _convert(code: str | Sequence[str] | None) -> str | Sequence[str] | None:
        if code is pd.NA or code == "" or code is None:  # If empty string or None or pd.NA, return None
            return None
        if isinstance(code, str):
            try:
                return mapping[code]
            except KeyError as e:
                raise ValueError(
                    f"Fant ikke alpha-3 kode: {code} i KLASS kodeliste (953)."
                ) from e
        if isinstance(code, Sequence):
            try:
                return [mapping[c] for c in code]
            except KeyError as e:
                raise ValueError(
                    f"Fant ikke alpha-3 koder: {code} i KLASS kodeliste (953)."
                ) from e

    return alpha_3_col.apply(_convert)


def load_verdensinndeling(year: int | str) -> dict[Hashable, str]:
    """Load and transform KLASS world division codes to regional groups."""
    # Read country codes correspondence
    landkoder_dict: dict[str, str] = _load_country_codes()

    # Read world division classification
    world_div_dict = (
        klass.KlassClassification(545)
        .get_codes(from_date=f"{year}-01-01", select_level=4)
        .data[["code", "parentCode"]]
        .set_index("code")["parent_code"]
        .str[-3:]
        .to_dict()
    )

    # Define and apply recoding rules
    recoding_rules: dict[str, str] = {
        "000": "1",
        "111": "2",
        "121": "3",
        "122": "3",
        "911": "5",
        "921": "5",
        # Note: all other values not in the dict will be changed to '4' by default
    }

    for key, value in world_div_dict.items():
        if key == "139":
            world_div_dict[key] = "4"
        elif value in recoding_rules:
            world_div_dict[key] = recoding_rules[value]
        else:
            world_div_dict[key] = "4"

    # Include any values in country codes, that may not be in world_div_dict
    for value in landkoder_dict.values():
        if value not in world_div_dict:
            # Add new key with ranking '4'
            world_div_dict[value] = "4"

    return world_div_dict
