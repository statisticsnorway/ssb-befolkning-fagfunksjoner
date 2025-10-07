import klass
import pandas as pd


def load_fylkesett(reference_date: str) -> dict[str, str]:
    """Load KLASS codelist for regions."""
    year: str = reference_date[:4]
    fylke_dict: dict[str, str] = (
        klass.KlassClassification(104)
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
        klass.KlassClassification(1)
        .get_codes(from_date=f"{year}-01-01", select_level=2)
        .to_dict()
    )
    gkrets_next_year: dict[str, str] = (
        klass.KlassClassification(1)
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
        klass.KlassClassification(131)
        .get_codes(from_date=f"{year}-01-01")
        .to_dict()
    )
    kommune_dict.pop("9999", None)
    kommune_dict["0000"] = "Sperret adresse"
    return kommune_dict


def load_landkoder() -> dict[str, str | None]:
    """Load KLASS correspondence table for country codes."""
    landkoder_dict: dict[str, str | None] = klass.KlassCorrespondence(953).to_dict()
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
        klass.KlassClassification(19)
        .get_codes(from_date=f"{year}-01-01")
        .to_dict()
    )
    sivilstand_dict["0"] = "Ukjent/uoppgitt"
    return sivilstand_dict


VERDENSINNDELING_RECODING_RULES: dict[str, str] = {
    "000": "1",
    "111": "2",
    "121": "3",
    "122": "3",
    "911": "5",
    "921": "5",
}

def load_verdensinndeling(reference_date: str) -> dict[str, str]:
    """Load and transform KLASS world division codes to regional groups."""
    year: str = reference_date[:4]
    landkoder_dict: dict[str, str] = load_landkoder()  # type: ignore
    world_div_df: pd.DataFrame = (
        klass.KlassClassification(545)
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
