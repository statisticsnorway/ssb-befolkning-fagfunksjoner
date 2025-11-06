from __future__ import annotations

import datetime
import functools
from typing import TypeAlias
from typing import cast
from typing import overload

import klass
import networkx
import pandas as pd
from klass.requests.klass_types import VersionPartType

from .change_mapping import _get_from_date
from .change_mapping import _get_to_date

_Code: TypeAlias = str


def _date_between(
    version: VersionPartType,
    date: datetime.date,
) -> bool:
    """Return True if date is between VersionPartType's time period.

    Includes from date, excludes to date.
    """
    v_from_date = _get_from_date(version)
    v_to_date = _get_to_date(version)

    return (v_from_date <= date) and (v_to_date is None or (date < v_to_date))


def _build_level_graph(
    version: klass.KlassVersion | klass.KlassCodes,
) -> networkx.DiGraph[_Code]:
    data = version.data
    graph: networkx.DiGraph[_Code] = networkx.DiGraph()

    graph.add_nodes_from(
        (code, {"level": int(level)})
        for code, level in zip(data["code"], data["level"], strict=False)
    )

    graph.add_edges_from(
        (parent_code, code)
        for code, parent_code in zip(data["code"], data["parentCode"], strict=False)
        if parent_code
    )

    return graph


def _find_index_and_label(
    index_or_label: int | str, version: klass.KlassVersion
) -> tuple[int, str]:
    if isinstance(index_or_label, str):
        level_label2index = cast(
            dict[str, int],
            {level["levelName"]: level["levelNumber"] for level in version.levels},
        )

        try:
            index = level_label2index[index_or_label]
        except KeyError:
            pass
        else:
            label = index_or_label
            return index, label

        try:
            index = int(index_or_label)
        except ValueError as e:
            error_message = (
                f"{index_or_label} is not a valid label in the Klass version.\n"
                f"Has labels {list(level_label2index.keys())}."
            )
            raise ValueError(error_message) from e

    else:
        index = index_or_label

    level_index2label = cast(
        dict[int, str],
        {level["levelNumber"]: level["levelName"] for level in version.levels},
    )

    try:
        label = level_index2label[index]
    except KeyError as e:
        error_message = (
            f"Klass version don't have a level with index {index}.\n"
            f"Has index {list(level_index2label.keys())}."
        )
        raise ValueError(error_message) from e

    return index, label


def _get_version_from_date(
    classification: klass.KlassClassification,
    date: datetime.date,
) -> klass.KlassVersion:
    try:
        version_meta = next(
            filter(
                functools.partial(
                    _date_between,
                    date=date,
                ),
                classification.versions,
            )
        )
    except StopIteration:
        error_message = f"Klass classification {classification.name} don't have a version that's valid on {date:%d.%m.%Y} "
        raise ValueError(error_message) from None

    return classification.get_version(version_meta["version_id"])


def _get_klass_level_map(
    version: klass.KlassVersion | klass.KlassCodes,
    to_levelindex: int,
) -> pd.Series:
    graph = _build_level_graph(version)

    level_mapping: set[tuple[str, str]] = set()

    codes_at_level = [
        code
        for (code, code_level) in graph.nodes(data="level")
        if code_level == to_levelindex
    ]
    for target_code in codes_at_level:
        children_codes = networkx.dfs_preorder_nodes(graph, target_code)

        level_mapping.update(
            (target_code, children_code) for children_code in children_codes
        )

    values, index = zip(*level_mapping, strict=True)
    series: pd.Series[str] = (
        pd.Series(values, index=pd.Index(index, name="codes"))
        .sort_values()
        .sort_index()
    )

    return series


@overload
def get_klass_level_map(
    to_level: int | str,
    *,
    version: None = None,
    classification: klass.KlassClassification = ...,
    date: datetime.date = ...,
) -> pd.Series: ...


@overload
def get_klass_level_map(
    to_level: int | str,
    *,
    version: klass.KlassVersion = ...,
    classification: None = None,
    date: None = None,
) -> pd.Series: ...


def get_klass_level_map(
    to_level: int | str,
    *,
    version: klass.KlassVersion | None = None,
    classification: klass.KlassClassification | None = None,
    date: datetime.date | None = None,
) -> pd.Series:
    """Creates a mapping to a level in a Klass version, from all children codes.

    Parameters:
        to_level: The level you want to aggregate up to. Either a index (like "1") or a label (like "NUTS 3").
        version: The Klass version you want to use, or
        classification: the Klass classification you want to use, and
        date: a date where the Klass version you want to use is valid.

    Returns:
        A series where the index contains children codes, and the values contains the targeted parent code.

    Raises:
        ValueError: If neither a Klass version is given or a class classification and a date is given.
                    If no Klass version is valid at the given date.
                    If the selected level is not found.
    """
    if not version:
        if classification is None or date is None:
            raise ValueError(
                "You must either submit a Klass version, or a Klass classfication and a date"
            )
        version = _get_version_from_date(classification, date)

    level_index, _ = _find_index_and_label(to_level, version)

    return _get_klass_level_map(version, level_index)


@overload
def aggregate_codes(
    codes: pd.Series,
    to_level: int | str,
    *,
    version: None = None,
    classification: klass.KlassClassification = ...,
    date: datetime.date = ...,
    keep_others: bool = ...,
) -> pd.Series: ...


@overload
def aggregate_codes(
    codes: pd.Series,
    to_level: int | str,
    *,
    version: klass.KlassVersion = ...,
    classification: None = None,
    date: None = None,
    keep_others: bool = ...,
) -> pd.Series: ...


def aggregate_codes(
    codes: pd.Series,
    to_level: int | str,
    *,
    version: klass.KlassVersion | None = None,
    classification: klass.KlassClassification | None = None,
    date: datetime.date | None = None,
    keep_others: bool = False,
) -> pd.Series:
    """Aggregates codes to selected level with Klass.

    Parameters:
        codes: A series with codes, that you want to aggregate.
        to_level: The level you want to aggregate up to. Either a index (like "1") or a label (like "NUTS 3").
        version: The Klass version you want to use, or
        classification: the Klass classification you want to use, and
        date: a date where the klass version you want to use is valid.
        keep_others: Do you want to keep codes that are above level you want to aggregate to or sentinel values?

    Returns:
        A series where the values are aggregated to the select level.

    Raises:
        ValueError: If neither a Klass version is given or a class classification and a date is given.
                    If no Klass version is valid at the given date.
                    If the selected level is not found.
    """
    if not version:
        if classification is None or date is None:
            raise ValueError(
                "You must either submit a Klass version, or a Klass classfication and a date"
            )
        version = _get_version_from_date(classification, date)

    level_index, level_label = _find_index_and_label(to_level, version)

    mapping = _get_klass_level_map(version, level_index)

    codes_at_level = codes.map(mapping)
    if keep_others:
        codes_at_level = codes_at_level.combine_first(codes)

    label_norm = level_label.lower().replace(" ", "_")
    name = (
        f"{codes.name}_{label_norm}"
        if any(label_norm.startswith(prefix) for prefix in ("nivå", "level"))
        else label_norm
    )

    return codes_at_level.rename(name)
