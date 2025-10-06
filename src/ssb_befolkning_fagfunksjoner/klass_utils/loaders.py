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
import functools
from itertools import chain
from itertools import pairwise
from typing import NamedTuple
from typing import cast

import networkx
import pandas as pd
from klass import KlassClassification
from klass import KlassCorrespondence
from klass import KlassVersion
from klass.requests.klass_types import VersionPartType

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
    to_date: str | datetime.date | None = None,
    from_date: str | datetime.date = datetime.date(1980, 1, 1),
    target_date: str | datetime.date | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load KLASS changes for municipalities."""
    # Read kommnr changes from KLASS
    if isinstance(to_date, str):
        to_date = datetime.date.fromisoformat(to_date)

    if isinstance(from_date, str):
        from_date = datetime.date.fromisoformat(from_date)

    if isinstance(target_date, str):
        target_date = datetime.date.fromisoformat(target_date)

    if target_date is None and to_date is not None:
        target_date = to_date

    classification = KlassClassification(131)
    kommnr_changes = get_changes_mapping(
        classification, target_date=target_date, to_date=to_date, from_date=from_date
    )

    # Drop non-changes
    kommnr_changes = kommnr_changes.loc[kommnr_changes.index != kommnr_changes]

    # Identify splits and drop them from kommnr changes
    mask = kommnr_changes.index.duplicated(keep=False)

    kommnr_splits = kommnr_changes.loc[mask].reset_index()

    kommnr_changes = kommnr_changes.loc[~mask].reset_index()

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


class _CodePoint(NamedTuple):
    code: str
    version: int


def _get_from_date(versjon: VersionPartType) -> datetime.date:
    return datetime.date.fromisoformat(versjon["validFrom"])


def _get_to_date(versjon: VersionPartType) -> datetime.date | None:
    try:
        return datetime.date.fromisoformat(versjon["validTo"])
    except KeyError:
        return None


def _dates_overlaps(
    versjon: VersionPartType,
    from_date: datetime.date,
    to_date: datetime.date | None,
) -> bool:
    v_from_date = _get_from_date(versjon)
    v_to_date = _get_to_date(versjon)

    return (v_to_date is None or (from_date < v_to_date)) and (
        to_date is None or (v_from_date <= to_date)
    )


def _build_change_graph(
    classification: KlassClassification,
    from_date: datetime.date,
    to_date: datetime.date | None,
) -> networkx.DiGraph:
    versions_meta = filter(
        functools.partial(
            _dates_overlaps,
            from_date=from_date,
            to_date=to_date,
        ),
        classification.versions,
    )

    versions_ids: set[int] = set()
    start_dates: dict[int, datetime.date] = {}
    versions: list[KlassVersion] = []

    for meta in versions_meta:
        version_id = meta[
            "version_id"
        ]  # pyright: ignore[reportTypedDictNotRequiredAccess]
        versions_ids.add(version_id)
        start_dates[version_id] = _get_from_date(meta)
        version = classification.get_version(version_id, language="nb")
        versions.append(version)

    graph = networkx.DiGraph()

    versions = sorted(
        versions,
        key=lambda version: start_dates[int(version.version_id)],
        reverse=False,
    )

    for version1, version2 in pairwise(versions):
        version1_kodes = cast(
            set[str], set(item["code"] for item in version1.classificationItems)
        )
        version2_kodes = cast(
            set[str], set(item["code"] for item in version2.classificationItems)
        )

        for code in version1_kodes & version2_kodes:
            edge = (
                _CodePoint(code, int(version1.version_id)),
                _CodePoint(code, int(version2.version_id)),
            )
            graph.add_edge(*edge)

    seen_change_tables_ides: set[int] = set()
    change_tables: list[KlassCorrespondence] = []

    for version in versions:
        for change_table_meta in filter(
            lambda v: v["sourceId"] in versions_ids and v["targetId"] in versions_ids,
            version.correspondenceTables,
        ):
            change_table_id = change_table_meta["id"]
            if change_table_id in seen_change_tables_ides:
                continue

            seen_change_tables_ides.add(change_table_id)
            change_tables.append(version.get_correspondence(change_table_id))

    for change_table in change_tables:
        backwards = (
            start_dates[change_table.sourceId] > start_dates[change_table.targetId]
        )
        for change in change_table.correspondence:
            if change["sourceCode"] is None or change["targetCode"] is None:
                continue
            edge = (
                _CodePoint(change["sourceCode"], change_table.sourceId),
                _CodePoint(change["targetCode"], change_table.targetId),
            )
            if backwards:
                edge = reversed(edge)
            graph.add_edge(*edge)

    return graph


def get_changes_mapping(
    classification: KlassClassification,
    target_date: datetime.date | None = None,
    from_date: datetime.date | None = None,
    to_date: datetime.date | None = None,
) -> pd.Series:
    """Normalize codes from different time to a specified target date based on KLASS change tables.

    Args:
        classification: A KlassClassification object.
        target_date: The date you want to normalize into.
        from_date: The oldest date in the dataset
        to_date: The newest date in the dataset

    Returns:
        A pandas series mapping existing to normalized codes, with existing codes as index labels, and normalized codes as values.
        The index can contain duplicated labels.

    Raises:
        ValueError: if the target_date is older than the from_date or older than the Klass classifcation if no from_date is set.
    """
    if target_date is None:
        target_date = max(map(_get_from_date, classification.versions))

    if from_date is None:
        from_date = min(map(_get_from_date, classification.versions))

    if target_date < from_date:
        raise ValueError(
            "Target date older than from date, or older than Klass classifcation"
        )

    graph = _build_change_graph(classification, from_date, to_date)

    target_version = next(
        filter(
            functools.partial(
                _dates_overlaps,
                from_date=target_date,
                to_date=target_date,
            ),
            classification.versions,
        )
    )

    target_version_id = int(target_version["version_id"])

    reverse_graph = graph.reverse()
    koorespondanser: set[tuple[str, str]] = set()
    for target_code_point in filter(lambda n: n.version == target_version_id, graph):
        older_code_points = networkx.dfs_preorder_nodes(graph, target_code_point)
        newer_code_points = networkx.dfs_preorder_nodes(
            reverse_graph, target_code_point
        )

        koorespondanser.update(
            (target_code_point.code, source_code_point.code)
            for source_code_point in chain(older_code_points, newer_code_points)
        )

    values, index = zip(*koorespondanser, strict=True)
    series = (
        pd.Series(values, index=pd.Index(index, name="old_code"), name="new_code")
        .sort_values()
        .sort_index()
    )
    return series
