import pandas as pd


def alderh(dob: pd.Series, event_date: pd.Series) -> pd.Series:
    """Creating the variable: `alderh`."""
    dob_dt = pd.to_datetime(arg=dob, format="%Y-%m-%d", errors="coerce")
    event_dt = pd.to_datetime(arg=event_date, format="%Y-%m-%d", errors="coerce")

    age = (
        event_dt.dt.year
        - dob_dt.dt.year
        - (
            # subtract 1 for dob > event_date in the same year
            (dob_dt.dt.month > event_dt.dt.month)
            | (
                (dob_dt.dt.month == event_dt.dt.month)
                & (dob_dt.dt.day > event_dt.dt.day)
            )
        )
    )

    return age


def alderu(dob: pd.Series, year: int | str) -> pd.Series:
    """Creating the variable: `alderu`."""
    dob_dt = pd.to_datetime(dob, format="%Y-%m-%d", errors="coerce")

    return int(year) - dob_dt.dt.year
