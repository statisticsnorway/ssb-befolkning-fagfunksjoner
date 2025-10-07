"""This module contains functions for loading KLASS codelists and correspondences.

Includes support for:
- fylker
- grunnkretser
- kommunenummer
- landkoder
- sivilstand
- verdensinndeling
"""

import datetime

import klass
import pandas as pd

from .klass_change_mapping import get_changes_mapping

# KLASS classification and correspondence IDs
FYLKE_ID = "104"
GRUNNKRETS_ID = "1"
KOMMUNE_ID = "131"
SIVILSTAND_ID = "19"
LANDKODER_CORRESPONDENCE_ID = "953"
VERDENSINNDELING_ID = "545"

# Recoding rules for world division
VERDENSINNDELING_RECODING_RULES: dict[str, str] = {
    "000": "1",
    "111": "2",
    "121": "3",
    "122": "3",
    "911": "5",
    "921": "5",
}


def load_fylkesett(reference_date: str) -> dict[str, str]:
    """Load KLASS codelist for regions."""
    year: str = reference_date[:4]
    fylke_dict: dict[str, str] = (
        klass.KlassClassification(FYLKE_ID)
        .get_codes(from_date=f"{year}-01-01")
        .to_dict()
    )
    fylke_dict.pop("99", None)
    fylke_dict["00"] = "Sperret adresse"
    return fylke_dict


def load_grunnkrets(reference_date: str) -> dict[str, dict[str, str]]:
    """Load KLASS codelist for grunnkretser for current and following year."""
    year: str = reference_date[:4]
    gkrets: dict[str, str] = (
        klass.KlassClassification(GRUNNKRETS_ID)
        .get_codes(from_date=f"{year}-01-01", select_level=2)
        .to_dict()
    )
    gkrets_next_year: dict[str, str] = (
        klass.KlassClassification(GRUNNKRETS_ID)
        .get_codes(
            from_date=f"{int(year) + 1}-01-01",
            include_future=True,
            select_level=2,
        )
        .to_dict()
    )
    return {"gkrets": gkrets, "gkrets_next_year": gkrets_next_year}


def load_kommnr(reference_date: str) -> dict[str, str]:
    """Load KLASS codelist for municipalities."""
    year: str = reference_date[:4]
    kommune_dict: dict[str, str] = (
        klass.KlassClassification(KOMMUNE_ID)
        .get_codes(from_date=f"{year}-01-01")
        .to_dict()
    )
    kommune_dict.pop("9999", None)
    kommune_dict["0000"] = "Sperret adresse"
    return kommune_dict


def load_kommnr_changes(
    to_date: str | datetime.date | None = None,
    from_date: str | datetime.date = datetime.date(1980, 1, 1),
    target_date: str | datetime.date | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load KLASS changes for municipalities.

    Returns:
    - singles (pd.DataFrame):
        Rows where an old municipality code maps to exactly one new code.
        Columns: ['old_kommnr', 'new_kommnr'].

    - splits (pd.DataFrame):
        Rows where an old municipality code maps to multiple new codes.
        Columns: ['old_kommnr', 'new_kommnr'].
    """
    # Normalise date-input
    if isinstance(to_date, str):
        to_date = datetime.date.fromisoformat(to_date)
    if isinstance(from_date, str):
        from_date = datetime.date.fromisoformat(from_date)
    if isinstance(target_date, str):
        target_date = datetime.date.fromisoformat(target_date)
    if target_date is None and to_date is not None:
        target_date = to_date

    kommnr_classification: klass.KlassClassification = klass.KlassClassification(131)

    # Read Series mapping old_code (index) -> new_code (value)
    kommnr_change_series = get_changes_mapping(
        kommnr_classification,
        target_date=target_date,
        to_date=to_date,
        from_date=from_date,
    )

    # Drop non-changes
    kommnr_change_series = kommnr_change_series.loc[
        kommnr_change_series.index != kommnr_change_series
    ]

    # Identify splits and drop them from `changes`
    is_split = kommnr_change_series.index.duplicated(keep=False)

    # Build DataFrames with clear column names
    def _as_df(s: pd.Series) -> pd.DataFrame:
        df = s.rename("new_kommnr").reset_index()
        df = df.rename(columns={"index": "old_kommnr"})
        return df

    kommnr_splits: pd.DataFrame = _as_df(kommnr_change_series[is_split])
    kommnr_changes: pd.DataFrame = _as_df(kommnr_change_series[~is_split])

    return kommnr_changes, kommnr_splits


def load_landkoder() -> dict[str, str | None]:
    """Load KLASS correspondence table for country codes."""
    landkoder_dict: dict[str, str | None] = klass.KlassCorrespondence(
        LANDKODER_CORRESPONDENCE_ID
    ).to_dict()
    manual_updates: dict[str, str] = {
        "ANT": "656",
        "CSK": "142",
        "DDR": "151",
        "PCZ": "669",
        "SCG": "125",
        "SKM": "546",
        "SUN": "135",
        "YUG": "125",
        "XXA": "990",
    }
    landkoder_dict.update(manual_updates)
    return landkoder_dict


def load_sivilstand(reference_date: str) -> dict[str, str]:
    """Load KLASS codelist for marital status."""
    year = reference_date[:4]
    sivilstand_dict: dict[str, str] = (
        klass.KlassClassification(SIVILSTAND_ID)
        .get_codes(from_date=f"{year}-01-01")
        .to_dict()
    )
    sivilstand_dict["0"] = "Ukjent/uoppgitt"
    return sivilstand_dict


def load_verdensinndeling(reference_date: str) -> dict[str, str]:
    """Load and transform KLASS world division codes to regional groups."""
    year: str = reference_date[:4]
    landkoder_dict: dict[str, str] = load_landkoder()  # type: ignore
    world_div_df: pd.DataFrame = (
        klass.KlassClassification(VERDENSINNDELING_ID)
        .get_codes(from_date=f"{year}-01-01", select_level=4)
        .data[["code", "parentCode"]]
    )
    world_div_dict: dict[str, str] = (
        world_div_df.set_index("code")["parentCode"].str[-3:].to_dict()
    )

    for key, value in world_div_dict.items():
        if key == "139":
            world_div_dict[key] = "4"
        elif value in VERDENSINNDELING_RECODING_RULES:
            world_div_dict[key] = VERDENSINNDELING_RECODING_RULES[value]
        else:
            world_div_dict[key] = "4"

    for value in landkoder_dict.values():
        if value not in world_div_dict:
            world_div_dict[value] = "4"

    return world_div_dict
