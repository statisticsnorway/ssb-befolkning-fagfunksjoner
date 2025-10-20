import pandas as pd
import pytest

from ssb_befolkning_fagfunksjoner.demographics.birth_rates import BirthRates


@pytest.fixture
def br_default() -> BirthRates:
    # sensible defaults
    return BirthRates(
        aldersgruppe_col="aldersgruppe",
        alder_col="alder",
        kjoenn_col="kjoenn",
        skala=1000,
        aldersgruppering=5,
        min_alder=15,
        max_alder=49,
        beregn_for_menn=False,  # kvinner
    )

@pytest.fixture
def df_start() -> pd.DataFrame:
    return pd.DataFrame({
        "kjoenn":   ["2", "2", "2", "1", "2", "2"],
        "alder":    [15,  18,  22,  22,  49,  50],   # En uttafor alder_max (50)
        "landsdel": ["A", "A", "A", "A", "B", "B"],
    })

@pytest.fixture
def df_slutt() -> pd.DataFrame:
    return pd.DataFrame({
        "kjoenn": ["2","2","2","2"],
        "alder":  [16, 24, 49, 15],
        "landsdel": ["A","A","B","B"],
    })

@pytest.fixture
def df_foedsler() -> pd.DataFrame:
    return pd.DataFrame({
        "kjoenn": ["2","2","2","2"],
        "alder":  [18, 22, 49, 16],
        "landsdel": ["A","A","B","B"],
    })


def test_valider_manglende_filter_kolonne(br_default: BirthRates, df_start: pd.DataFrame) -> None:
    df = df_start.drop(columns=["alder"])
    with pytest.raises(ValueError):
        br_default._filtrer_og_lag_aldersgrupper(df)
    

def test_kjoenn_filter(br_default: BirthRates, df_start: pd.DataFrame) -> None:
    df = br_default._filtrer_og_lag_aldersgrupper(df_start)
    assert (df["kjoenn"].astype(str) == "2").all()


def test_aldersgruppering(br_default: BirthRates, df_start: pd.DataFrame) -> None:
    with pytest.warns(UserWarning):
        df = br_default._filtrer_og_lag_aldersgrupper(df_start)

    assert df["alder"].dtype == "Int64"
    assert set(df["aldersgruppe"]) == {"15-19", "15-19", "20-24", "20-24", "45-49"}


def test_normaliser_grupperingsvariabler_none(br_default: BirthRates) -> None:
    cols = br_default._normaliser_grupperingsvariabler(None)
    assert cols == ["aldersgruppe"]

def test_normaliser_grupperingsvariabler_str(br_default: BirthRates) -> None:
    cols = br_default._normaliser_grupperingsvariabler("landsdel")
    assert cols == ["landsdel", "aldersgruppe"]

def test_normaliser_grupperingsvariabler_list(br_default: BirthRates) -> None:
    cols = br_default._normaliser_grupperingsvariabler(["aldersgruppe","landsdel"])
    assert cols == ["landsdel", "aldersgruppe"]


def test_mfm(br_default: BirthRates, df_start: pd.DataFrame, df_slutt: pd.DataFrame) -> None:
    cols = br_default._normaliser_grupperingsvariabler("landsdel")
    mfm = br_default._beregn_middelfolkemengde(df_start, df_slutt, cols)

    # required columns
    for c in ["n_df_start","n_df_slutt","middelfolkemengde","landsdel","aldersgruppe"]:
        assert c in mfm.columns

    # no NaNs in counts after fill
    assert mfm["n_df_start"].isna().sum() == 0
    assert mfm["n_df_slutt"].isna().sum() == 0


def test_foedselsrater(br_default: BirthRates, df_start: pd.DataFrame, df_slutt: pd.DataFrame, df_foedsler: pd.DataFrame) -> None:
    
    forventet_output = pd.DataFrame({
        "aldersgruppe":      ["15-19", "15-19", "20-24", "20-24", "45-49", "45-29"],
        "landsdel":          ["A",     "B",     "A",     "B",     "A",     "B"],
        "n_df_start":        [2,       0,       2,        0,       0,       1],
        "n_df_slutt":        [1,       1,       1,        0,       0,       1],
        "middelfolkemengde": [1,       0.5,     1,        0,       0,       1],
        "n_foedsler":        [1,       1,       1,        0,       0,       1],
        "foedselsrate":      [1000,    2000,    1000,     0,       0,       1000]
    })
    df = br_default.beregn_foedselsrate(df_start, df_slutt, df_foedsler, "landsdel")

    for c in ["n_df_start", "n_df_slutt", "middelfolkemengde", "n_foedsler", "foedselsrate"]:
        assert c in df.columns
    
    assert (df == forventet_output)
