import datetime
import pandas as pd
import klass

from ..klass_utils.change_mapping import get_klass_change_mapping

__all__ = ["get_kommnr_changes"]


def get_kommnr_changes(
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
        df = s.rename("new_kommnr").reset_index()
        df = df.rename(columns={"index": "old_kommnr"})
        return df

    kommnr_splits: pd.DataFrame = _as_df(kommnr_change_series[is_split])
    kommnr_changes: pd.DataFrame = _as_df(kommnr_change_series[~is_split])

    return kommnr_changes, kommnr_splits
