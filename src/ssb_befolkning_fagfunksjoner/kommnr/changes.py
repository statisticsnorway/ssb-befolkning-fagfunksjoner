import datetime

import klass
import pandas as pd

from ..klass_utils.change_mapping import get_klass_change_mapping

__all__ = ["get_kommnr_changes"]


def get_kommnr_changes(
    from_date: str | datetime.date = datetime.date(1980, 1, 1),
    to_date: str | datetime.date | None = None,
    target_date: str | datetime.date | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load municipality code (kommnr) changes from KLASS.

    Args:
        from_date : str | datetime.date, default=datetime.date(1980, 1, 1)
            Lower bound date for change history to include. Defaults to 01-01-1980.
        to_date : str | datetime.date | None, default=None
            Upper bound date for change history to include. Defaults to today.
        target_date : str | datetime.date | None, default=None
            Target date for municipality code mappings. Defaults to today.
    
    Returns:
        tuple[pd.DataFrame, pd.DataFrame]
            A tuple ``(changes, splits)`` with mappings from `old_code` to `new_code`. 
            Split into codes that map to exactly one new code, and codes that map to multiple new codes. 

    Raises:
        ValueError 
            If any of the input parameters are not the correct type. 
    """
    # Input validation
    for name, val in {
        "from_date": from_date,
        "to_date": to_date,
        "target_date": target_date,
    }.items():
        if val is not None and not isinstance(val, str | datetime.date):
            raise ValueError(
                f"Invalid type for {name}: {type(val).__name__}. Expected str or datetime.date."
            )

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
    kommnr_change_series = get_klass_change_mapping(
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

    def _as_df(s: pd.Series) -> pd.DataFrame:
        df = s.rename("new_code").reset_index()
        df = df.rename(columns={"index": "old_code"})
        return df

    kommnr_splits: pd.DataFrame = _as_df(kommnr_change_series[is_split])
    kommnr_changes: pd.DataFrame = _as_df(kommnr_change_series[~is_split])

    return kommnr_changes, kommnr_splits
