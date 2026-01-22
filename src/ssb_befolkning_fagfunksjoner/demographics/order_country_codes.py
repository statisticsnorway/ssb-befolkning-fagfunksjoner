from __future__ import annotations

from typing import Sequence
from datetime import datetime

from ssb_befolkning_fagfunksjoner.klass_utils.loaders import load_verdensinndeling


def order_citizenships(
    country_codes: Sequence[str], 
    *, 
    dates: Sequence[str] | None = None, 
    select_first: bool = False, 
    year: int | str = datetime.today().year
) -> tuple[list[Sequence[str]], list[Sequence[str]]] | list[Sequence[str]]:
    """Reorders country code columns for each row based on a KLASS ranking."""
    # Get ranking dictionary 
    ranking = load_verdensinndeling(year)

    # Apply ranking
    if dates is not None:
        ordered = [_sort_by_ranking_multiple(ranking, c, d) for c, d in zip(country_codes, dates)]

        if select_first:
            sorted_codes = [c[0:1] for c, _ in ordered]
            sorted_dates = [d[0:1] for _, d in ordered]
            return sorted_codes, sorted_dates

        sorted_codes = [c for c, _ in ordered]
        sorted_dates = [d for _, d in ordered]
        return sorted_codes, sorted_dates

    else:
        ordered = [_sort_by_ranking(ranking, c) for c in country_codes]

        if select_first:
            return [c[0:1] for c in ordered]

        return ordered


def _sort_by_ranking_multiple(ranking: dict[str, int], c: Sequence[str], d: Sequence[str]) -> tuple[Sequence[str], Sequence[str]]:
    pairs = list(zip(c, d))
    sorted_pairs = sorted(
        pairs, key=lambda x: ranking.get(x[0], float('inf'))
    )

    # Unpack 
    sorted_codes = [p[0] for p in sorted_pairs]
    sorted_dates = [p[1] for p in sorted_pairs]
    return sorted_codes, sorted_dates


def _sort_by_ranking(ranking: dict[str, int], c: Sequence[str]) -> Sequence[str]:
    sorted_codes = sorted(
        c, key=lambda code: ranking.get(code, float('inf'))
    )
    return sorted_codes
