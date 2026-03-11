from collections.abc import Sequence
from typing import cast

import pandas as pd
from pandas.api.typing import NAType

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

    def _convert(code: str | Sequence[str] | None | NAType) -> str | Sequence[str] | None:
        if (
            code is pd.NA or code is None
        ):  # If empty string or None or pd.NA, return None
            return None
        if isinstance(code, str):
            try:
                return mapping[code]
            except KeyError as e:
                raise ValueError(
                    f"Fant ikke alpha-3 kode: {code} i KLASS kodeliste (953)."
                ) from e

        try:
            return [mapping[c] for c in cast(Sequence[str], code)]
        except KeyError as e:
            raise ValueError(
                f"Fant ikke alpha-3 koder: {code} i KLASS kodeliste (953)."
            ) from e

    return alpha_3_col.apply(_convert)
