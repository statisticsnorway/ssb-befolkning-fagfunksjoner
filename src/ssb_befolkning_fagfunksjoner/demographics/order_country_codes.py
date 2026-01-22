from collections.abc import Sequence
from datetime import datetime

from ssb_befolkning_fagfunksjoner.klass_utils.loaders import load_verdensinndeling


def sorter_landkoder(
    country_codes: Sequence[str],
    *,
    dates: Sequence[str] | None = None,
    select_first: bool = False,
    year: int | str = datetime.today().year,
) -> tuple[list[Sequence[str]], list[Sequence[str]]] | list[Sequence[str]]:
    """Reorders country codes based on KLASS regional priority ranking.

    Parameters
    ----------
    country_codes : Sequence[str]
        Sequence of country code lists to reorder.
    dates : Sequence[str] | None, optional
        Optional date lists corresponding to country codes.
        If provided, dates are reordered to match country code order.
    select_first : bool, default False
        If True, return only the highest-priority code (and date) per row.
    year : int | str, default current year
        Year for loading the appropriate KLASS classification.

    Returns:
    -------
    tuple[list, list] | list
        If dates provided: (ordered_codes, ordered_dates)
        If no dates: ordered_codes
        If select_first=True, each sublist contains only one element.
    """
    # Validate inputs
    if dates is not None and len(country_codes) != len(dates):
        raise ValueError(
            f"Length mismatch: country_codes has {len(country_codes)} elements "
            f"but dates has {len(dates)} elements."
        )

    # Get ranking dictionary
    ranking = load_verdensinndeling(year)

    # Apply ranking with dates
    if dates is not None:
        ordered = [
            _sort_by_ranking_multiple(ranking, code_list, date_list)
            for code_list, date_list in zip(country_codes, dates)
        ]

        if select_first:
            sorted_codes = [sorted_code_list[0:1] for sorted_code_list, _ in ordered]
            sorted_dates = [sorted_date_list[0:1] for _, sorted_date_list in ordered]
            return sorted_codes, sorted_dates

        sorted_codes = [sorted_code_list for sorted_code_list, _ in ordered]
        sorted_dates = [sorted_date_list for _, sorted_date_list in ordered]
        return sorted_codes, sorted_dates

    # Apply ranking without dates
    else:
        ordered = [_sort_by_ranking(ranking, code_list) for code_list in country_codes]

        if select_first:
            return [sorted_code_list[0:1] for sorted_code_list in ordered]

        return ordered


def _sort_by_ranking_multiple(
    ranking: dict[str, int], codes: Sequence[str], dates: Sequence[str]
) -> tuple[Sequence[str], Sequence[str]]:
    """Sort country codes and dates by ranking priority."""
    # Handle empty Sequences
    if not codes:
        return codes, dates

    pairs = list(zip(codes, dates))
    sorted_pairs = sorted(pairs, key=lambda x: ranking.get(x[0], float("inf")))

    # Unpack
    sorted_codes = [code for code, _ in sorted_pairs]
    sorted_dates = [date for _, date in sorted_pairs]

    return sorted_codes, sorted_dates


def _sort_by_ranking(ranking: dict[str, int], codes: Sequence[str]) -> Sequence[str]:
    """Sort country codes by ranking priority."""
    # Handle empty Sequences
    if not codes:
        return codes

    return sorted(codes, key=lambda code: ranking.get(code, float("inf")))
