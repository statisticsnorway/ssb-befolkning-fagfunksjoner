from typing import cast

import klass


def load_komm_nr(year: int | str) -> dict[str, str]:
    """Load KLASS codelist for municipalities."""
    kommune_dict: dict[str, str] = (
        klass.KlassClassification(131).get_codes(from_date=f"{year}-01-02").to_dict()
    )

    # Handle missing values
    kommune_dict.pop("9999", None)
    kommune_dict["0000"] = "Sperret adresse"

    return kommune_dict


def load_country_codes() -> dict[str, str]:
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


def load_verdensinndeling(year: int | str) -> dict[str, int]:
    """Load and transform KLASS world division codes to regional groups."""
    # Read country codes correspondence
    landkoder_dict = load_country_codes()

    # Read world division classification
    world_div_dict = (
        klass.KlassClassification(545)
        .get_codes(from_date=f"{year}-01-01", select_level=4)
        .data[["code", "parentCode"]]
        .set_index("code")["parentCode"]
        .str[-3:]
        .to_dict()
    )

    # Define and apply recoding rules
    recoding_rules = {
        "000": 1,
        "111": 2,
        "121": 3,
        "122": 3,
        "911": 5,
        "921": 5,
        # Note: all other values not in the dict will be changed to '4' by default
    }
    recoded_dict = {
        k: recoding_rules.get(v, 4)
        for k, v in cast(dict[str, str], world_div_dict).items()
    }

    # Set UK outside European group
    recoded_dict["139"] = 4

    # Include any values in country codes, that may not be in world_div_dict
    for value in landkoder_dict.values():
        if value not in recoded_dict:
            # Add new key with ranking '4'
            recoded_dict[value] = 4

    return recoded_dict
