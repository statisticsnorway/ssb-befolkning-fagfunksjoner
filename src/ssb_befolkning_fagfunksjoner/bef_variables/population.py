import pandas as pd


def alderh(dob: pd.Series, event_date: pd.Series) -> pd.Series:
    """Lager variabelen `alderh`."""
    dob = pd.to_datetime(dob, format="%Y-%m-%d", errors="coerce")
    event_date = pd.to_datetime(event_date, format="%Y-%m-%d", errors="coerce")

    age = (
        event_date.dt.year
        - dob.dt.year
        - (
            # subtract 1 for dob > event_date in the same year
            (dob.dt.month > event_date.dt.month)
            | ((dob.dt.month == event_date.dt.month) & (dob.dt.day > event_date.dt.day))
        )
    )

    return age
