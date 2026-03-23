from collections.abc import Sequence

import pandas as pd

from ssb_befolkning_fagfunksjoner.klass_utils.loaders import load_country_codes


def map_to_country_codes(alpha_3_col: pd.Series) -> pd.Series:
    """Convert a Series of ISO alpha-3 codes to SSB-3 codes.

    Parameters:
        alpha_3_col: pd.Series
            A pandas series of citizenships that may contain scalars (e.g., "NOR") or sequences (e.g., ["NOR", "SWE"]).

    Returns:
        pd.Series
    """
    mapping: dict[str, str] = load_country_codes()

    def _convert(code: Sequence[str] | str) -> Sequence[str] | None:
        if isinstance(code, str):
            return mapping[code]

        return [mapping[c] for c in code]

    return alpha_3_col.map(_convert, na_action="ignore")
