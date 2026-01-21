from __future__ import annotations

import datetime
import enum
import functools
from collections.abc import Iterable
from itertools import chain
from itertools import pairwise
from typing import NamedTuple
from typing import cast

import klass
import networkx
import pandas as pd
from klass.requests.klass_types import CorrespondenceTablesType
from klass.requests.klass_types import VersionPartType

__all__ = ["get_klass_change_mapping"]


class _CodePoint(NamedTuple):
    code: str
    version: int


class _CessionType(enum.Enum):
    NO_CESSION = enum.auto()
    CESSATION_WHOLE = enum.auto()
    CESSATION_PART_TO_NEW = enum.auto()
    CESSATION_PART_TO_EXISTING = enum.auto()
    ADJUSTMENT_PART_TO_NEW = enum.auto()
    ADJUSTMENT_PART_TO_EXISTING = enum.auto()
    BORDER_CHANGE = enum.auto()


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
    """Return True if VersionPartType's time period [v_from_date, v_to_date] overlaps with input [from_date, to_date]."""
    v_from_date = _get_from_date(version)
    v_to_date = _get_to_date(version)

    return (v_to_date is None or (from_date < v_to_date)) and (
        to_date is None or (v_from_date <= to_date)
    )


def _build_change_graph(
    classification: klass.KlassClassification,
    from_date: datetime.date,
    to_date: datetime.date | None = None,
) -> networkx.DiGraph[_CodePoint]:
    """Construct a directed graph representing relations between municipality codes across KlassClassification versions.

    Parameters:
        classification: KlassClassification
            Classification object, typically ID = 131 for municipality codes.
        from_date: datetime.date
            Date for earliest version to include in the graph.
        to_date: datetime.date
            Date for latest version to include in graph. If None, all later versions are included.

    Returns:
        networkx.DiGraph
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
    graph: networkx.DiGraph[_CodePoint] = networkx.DiGraph()

    # Sort versions by start dates using start_dates mapping version_id -> validFrom date
    versions = sorted(
        versions,
        key=lambda version: start_dates[int(version.version_id)],
        reverse=False,
    )

    # Create overlapping pairs of consecutive elements
    for version1, version2 in pairwise(versions):
        version1_codes = cast(
            set[str], {item["code"] for item in version1.classificationItems}
        )
        version2_codes = cast(
            set[str], {item["code"] for item in version2.classificationItems}
        )

        # Loop over codes in intersection and add edges `old_code -> new_code`
        for code in version1_codes & version2_codes:
            edge = (
                _CodePoint(code, int(version1.version_id)),
                _CodePoint(code, int(version2.version_id)),
            )
            graph.add_edge(*edge, cession_type=_CessionType.NO_CESSION)

    # Get correspondence tables between filtered versions
    seen_change_tables_ides: set[int] = set()
    change_tables: list[klass.KlassCorrespondence] = []

    for version in versions:
        select_cts: list[CorrespondenceTablesType] = [
            ct
            for ct in version.correspondenceTables
            if int(ct["sourceId"]) in versions_ids
            and int(ct["targetId"]) in versions_ids
        ]
        for change_table_meta in select_cts:
            change_table_id = int(change_table_meta["id"])
            if change_table_id in seen_change_tables_ides:
                continue

            seen_change_tables_ides.add(change_table_id)
            change_tables.append(version.get_correspondence(change_table_id))

    for change_table in change_tables:
        # Check direction of correspondence
        backwards = (
            start_dates[change_table.sourceId] > start_dates[change_table.targetId]
        )

        # Read changes from correspondence tables and add edges
        for change in change_table.correspondence:
            if change["sourceCode"] is None or change["targetCode"] is None:
                continue
            edge: Iterable[_CodePoint] = (
                _CodePoint(change["sourceCode"], change_table.sourceId),
                _CodePoint(change["targetCode"], change_table.targetId),
            )
            if backwards:
                edge = reversed(edge)
            graph.add_edge(*edge, cession_type=None)

    _label_changes(graph)
    return graph


def _label_changes(graph: networkx.DiGraph[_CodePoint]) -> None:
    """Label graph edges with a "cession type".

    Since the Klass API is missing metadata abut the type of change, like the SCB Regina API,
    we try to interfere the type of cession here.
    The algorithm may mislabel changes as a cessation, if there is boarder changes and code changes at the same time.
    """
    get_cession_type = networkx.get_edge_attributes(graph, "cession_type")
    edges_missing_label: Iterable[tuple[_CodePoint, _CodePoint]] = filter(
        lambda e: get_cession_type[e] is None, graph.edges
    )
    for edge in edges_missing_label:
        v, u = edge

        out_degree = graph.out_degree(v)
        in_degree = graph.in_degree(u)

        old_codes = set(p.code for p in graph.predecessors(u))
        new_codes = set(s.code for s in graph.successors(v))

        if in_degree == 1 and out_degree == 1:
            graph.edges[edge]["cession_type"] = _CessionType.NO_CESSION

        elif v.code == u.code:
            graph.edges[edge]["cession_type"] = _CessionType.BORDER_CHANGE

        elif out_degree == 1:
            graph.edges[edge]["cession_type"] = _CessionType.CESSATION_WHOLE

        elif v.code not in new_codes and u.code not in old_codes:
            graph.edges[edge]["cession_type"] = _CessionType.CESSATION_PART_TO_NEW

        elif v.code not in new_codes:
            graph.edges[edge]["cession_type"] = _CessionType.CESSATION_PART_TO_EXISTING

        elif u.code not in old_codes:
            graph.edges[edge]["cession_type"] = _CessionType.ADJUSTMENT_PART_TO_NEW

        else:
            graph.edges[edge]["cession_type"] = _CessionType.ADJUSTMENT_PART_TO_EXISTING


def get_klass_change_mapping(
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
            "Target date older than from date, or older than KLASS classifcation"
        )

    # Get directed graph `old_code -> new_code`
    graph = _build_change_graph(classification, from_date, to_date)

    # To ignore minor boarder changes we filter away cession type ADJUSTMENT_PART_TO_EXISTING
    get_cession_type = networkx.get_edge_attributes(graph, "cession_type")
    graph = networkx.subgraph_view(
        graph,
        filter_edge=lambda *e: get_cession_type[e]
        is not _CessionType.ADJUSTMENT_PART_TO_EXISTING,
    )

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
    target_version_id = int(target_version["version_id"])

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
            for source_cp in chain(
                descendant_cps, ancestor_cps
            )  # iterator over descendant_cps + ancestor_cps
        )

    # Construct Series from correspondences
    values, index = zip(*correspondences, strict=True)
    series: pd.Series[str] = (
        pd.Series(values, index=pd.Index(index, name="old_code"), name="new_code")
        .sort_values()
        .sort_index()
    )

    return series
