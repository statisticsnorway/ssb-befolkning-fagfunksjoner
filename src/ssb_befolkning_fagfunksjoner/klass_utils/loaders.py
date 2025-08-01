"""This module contains functions for loading KLASS codelists and correspondences.

Includes support for:
- fylker
- grunnkretser
- kommunenummer
- landkoder
- sivilstand
- verdensinndeling
"""

import pandas as pd
from klass import KlassClassification
from klass import KlassCorrespondence

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
        KlassClassification(FYLKE_ID).get_codes(from_date=f"{year}-01-01").to_dict()
    )

    fylke_dict.pop("99", None)

    fylke_dict["00"] = "Sperret adresse"

    return fylke_dict


def load_grunnkrets(reference_date: str) -> dict[str, dict[str, str]]:
    """Load KLASS codelist for grunnkretser for current and following year."""
    year: str = reference_date[:4]

    gkrets: dict[str, str] = (
        KlassClassification(GRUNNKRETS_ID)
        .get_codes(from_date=f"{year}-01-01", select_level=2)
        .to_dict()
    )

    gkrets_next_year: dict[str, str] = (
        KlassClassification(GRUNNKRETS_ID)
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
        KlassClassification(KOMMUNE_ID).get_codes(from_date=f"{year}-01-01").to_dict()
    )

    kommune_dict.pop("9999", None)

    kommune_dict["0000"] = "Sperret adresse"

    return kommune_dict


def load_kommnr_changes(
    to_date: str, from_date: str = "1980-01-01"
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load KLASS changes for municipalities."""
    # Read kommnr changes from KLASS
    kommnr_changes: pd.DataFrame = (
        KlassClassification(KOMMUNE_ID)
        .get_changes(from_date=from_date, to_date=to_date)[
            ["oldCode", "newCode", "changeOccurred"]
        ]
        .sort_values("changeOccurred", ascending=True)
    )

    # Drop non-changes
    kommnr_changes = kommnr_changes[
        kommnr_changes["oldCode"] != kommnr_changes["newCode"]
    ]

    # Identify splits and drop them from kommnr changes
    kommnr_splits = kommnr_changes.loc[
        kommnr_changes.duplicated(subset=["oldCode", "changeOccurred"], keep=False)
    ]
    kommnr_changes = kommnr_changes.loc[
        ~kommnr_changes["oldCode"].isin(kommnr_splits["oldCode"].drop_duplicates()),
        ["oldCode", "newCode"],
    ]

    return kommnr_changes, kommnr_splits


def load_landkoder() -> dict[str, str | None]:
    """Load KLASS correspondence table for country codes."""
    landkoder_dict: dict[str, str | None] = KlassCorrespondence(
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
        KlassClassification(SIVILSTAND_ID)
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
        KlassClassification(VERDENSINNDELING_ID)
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
