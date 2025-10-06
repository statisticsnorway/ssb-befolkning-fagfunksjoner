"""This module contains functions for loading KLASS codelists and correspondences.

Includes support for:
- fylker
- grunnkretser
- kommunenummer
- landkoder
- sivilstand
- verdensinndeling
"""
from __future__ import annotations
import datetime
import functools
from itertools import chain, pairwise
from typing import NamedTuple, cast

import klass
import networkx
import pandas as pd
from klass.requests.klass_types import CorrespondenceTablesType, VersionPartType

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
        klass.KlassClassification(FYLKE_ID).get_codes(from_date=f"{year}-01-01").to_dict()
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
        klass.KlassClassification(KOMMUNE_ID).get_codes(from_date=f"{year}-01-01").to_dict()
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
        kommnr_classification, target_date=target_date, to_date=to_date, from_date=from_date
    )

    # Drop non-changes
    kommnr_change_series = kommnr_change_series.loc[kommnr_change_series.index != kommnr_change_series]

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


class _CodePoint(NamedTuple):
    code: str
    version: int


def _get_from_date(version: VersionPartType) -> datetime.date:
    return datetime.date.fromisoformat(version["validFrom"])


def _get_to_date(version: VersionPartType) -> datetime.date | None:
    try:
        return datetime.date.fromisoformat(version["validTo"])
    except KeyError:
        return None


def _dates_overlap(
    version: VersionPartType,
    from_date: datetime.date,
    to_date: datetime.date | None,
) -> bool:
    """
    Return True if VersionPartType's time period [v_from_date, v_to_date] overlaps with input [from_date, to_date].
    """
    v_from_date = _get_from_date(version)
    v_to_date = _get_to_date(version)

    return (v_to_date is None or (from_date < v_to_date)) and (
        to_date is None or (v_from_date <= to_date)
    )


def _build_change_graph(
    classification: klass.KlassClassification,
    from_date: datetime.date,
    to_date: datetime.date | None,
) -> networkx.DiGraph:
    """
    Construct a directed graph representing relations between municipality codes across KlassClassification versions.

    Parameters:
    - classification (KlassClassification): Classification object, typically ID = 131 for municipality codes.
    - from_date (datetime.date): Date for earliest version to include in the graph.
    - to_date (datetime.date): Date for latest version to include in graph. If None, all later versions are included.

    Returns:
    - networkx.DiGraph: Directed graph 
    """
    # Filter on which versions to include in graph
    versions_meta = filter(
        functools.partial(_dates_overlap, from_date=from_date, to_date=to_date),
        classification.versions,
    )

    versions_ids: set[int] = set()
    start_dates: dict[int, datetime.date] = {}
    versions: list[klass.KlassVersion] = []

    for meta in versions_meta:
        version_id = meta[
            "version_id"
        ]  # pyright: ignore[reportTypedDictNotRequiredAccess]
        versions_ids.add(version_id)
        start_dates[version_id] = _get_from_date(meta)
        version = classification.get_version(version_id, language="nb")
        versions.append(version)

    # Initialise directed graph
    graph: networkx.DiGraph = networkx.DiGraph()

    # Sort versions by start dates using start_dates mapping version_id -> validFrom date
    versions = sorted(
        versions,
        key=lambda version: start_dates[int(version.version_id)],
        reverse=False,
    )

    # Create overlapping pairs of consecutive elements
    for version1, version2 in pairwise(versions):
        version1_codes = cast(set[str], {item["code"] for item in version1.classificationItems})
        version2_codes = cast(set[str], {item["code"] for item in version2.classificationItems})

        # Loop over codes in intersection and add edges `old_code -> new_code`
        for code in version1_codes & version2_codes:
            edge = (
                _CodePoint(code, int(version1.version_id)),
                _CodePoint(code, int(version2.version_id)),
            )
            graph.add_edge(*edge)


    # Get correspondence tables between filtered versions
    seen_change_tables_ides: set[int] = set()
    change_tables: list[klass.KlassCorrespondence] = []

    for version in versions:
        select_cts: list[CorrespondenceTablesType] = [
            ct for ct in version.correspondenceTables
            if int(ct["sourceId"]) in versions_ids and int(ct["targetId"]) in versions_ids  # type: ignore
        ]
        for change_table_meta in select_cts:
            change_table_id = int(change_table_meta["id"])  # type: ignore
            if change_table_id not in seen_change_tables_ides:
                seen_change_tables_ides.add(change_table_id)
                change_tables.append(version.get_correspondence(change_table_id))

    for change_table in change_tables:
        # Check direction of correspondence
        backwards = (start_dates[change_table.sourceId] > start_dates[change_table.targetId])

        # Read changes from correspondence tables and add edges
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
    classification: klass.KlassClassification,
    target_date: datetime.date | None = None,
    from_date: datetime.date | None = None,
    to_date: datetime.date | None = None,
) -> pd.Series:
    """Normalise codes from different time to a specified target date based on KLASS change tables.

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
    # Normalise date input
    if target_date is None:
        target_date = max(map(_get_from_date, classification.versions))
    if from_date is None:
        from_date = min(map(_get_from_date, classification.versions))
    if target_date < from_date:
        raise ValueError(
            "Target date older than from date, or older than Klass classifcation"
        )

    # Get directed graph `old_code -> new_code`
    graph = _build_change_graph(classification, from_date, to_date)

    # Filter to version valid on target date (next(iterator) selects first element from iterator)
    target_version = next(
        filter(
            functools.partial(
                _dates_overlap,
                from_date=target_date,
                to_date=target_date,
            ),
            classification.versions,
        )
    )
    target_version_id = int(target_version["version_id"])  # type: ignore

    # Reverse graph to `new_code -> old_code`
    reverse_graph = graph.reverse()

    # Create correspondences to target date
    correspondences: set[tuple[str, str]] = set()

    # Loop over all nodes (code points) in the target version
    target_cps = [n for n in graph if n.version == target_version_id]
    for target_cp in target_cps:
        # Get all code points connected to target as descendants and ancestors
        descendant_cps = networkx.dfs_preorder_nodes(graph, target_cp)
        ancestor_cps = networkx.dfs_preorder_nodes(reverse_graph, target_cp)

        # For the target node, relate it to all its connected codes across time
        correspondences.update(
            (target_cp.code, source_cp.code)
            for source_cp in chain(descendant_cps, ancestor_cps)  # iterator over descendant_cps + ancestor_cps
        )

    # Construct Series from correspondences
    values, index = zip(*correspondences, strict=True)
    series = (
        pd.Series(values, index=pd.Index(index, name="old_code"), name="new_code")
        .sort_values()
        .sort_index()
    )

    return series
