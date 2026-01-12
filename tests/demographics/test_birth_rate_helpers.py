import numpy as np
import pandas as pd
import pytest
from pandas.testing import assert_series_equal

from ssb_befolkning_fagfunksjoner.demographics.birth_rates import BirthRates


@pytest.fixture
def br_default() -> BirthRates:
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
def mock_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "kjoenn": ["2", "2", "2", "2", "2", "2", "2", "1", "1"],
            "alder": [14, 15, 18, 22, 49, 50, np.nan, 64, 30],
            "landsdel": ["A", "A", "A", "A", "B", "B", "A", "B", "A"],
        }
    )


def test_filter_og_aldersgruppering(
    br_default: BirthRates, mock_df: pd.DataFrame
) -> None:
    """Tester hjelpefunksjonen '_filtrer_og_lag_aldersgrupper'.

    Forventet oppførsel:
    - Beholder kun rader med 'kjoenn' == "2"
    - Filtrerer bort rader utenfor aldersintervallet ('min_alder', 'max_alder'), og NaN
    - Oppretter kolonnen 'aldersgruppe' med 5-års intervaller
    Skal filtrere til kun kvinner, [min_alder, max_alder] (inklusivt).
    """
    resultat = br_default._filtrer_og_lag_aldersgrupper(mock_df)

    # Resultat bør ha bare kvinner
    assert not (resultat[br_default.kjoenn_col] == "1").any()

    # Sjekk filtrering av aldre
    assert resultat[br_default.alder_col].min() >= br_default.min_alder
    assert resultat[br_default.alder_col].max() <= br_default.max_alder
    assert not resultat[br_default.alder_col].isna().any()

    # Sjekk aldersgruppering
    forventet_aldersgruppe = pd.Series(
        ["15-19", "15-19", "20-24", "45-49"],
        name=br_default.aldersgruppe_col,
        dtype="string",
    )
    assert_series_equal(
        resultat[br_default.aldersgruppe_col].reset_index(drop=True),
        forventet_aldersgruppe,
    )

    # Sjekk kolonner i output
    for c in list(mock_df.columns) + [br_default.aldersgruppe_col]:
        assert c in resultat.columns


def test_manglende_kolonne_error(br_default: BirthRates, mock_df: pd.DataFrame):
    df = mock_df.drop(columns=[br_default.alder_col])
    with pytest.raises(ValueError):
        br_default._filtrer_og_lag_aldersgrupper(df)


def test_idempotency(br_default: BirthRates, mock_df: pd.DataFrame):
    """Å kjøre helperen to ganger skal ikke endre resultatet (idempotent)."""
    out1 = br_default._filtrer_og_lag_aldersgrupper(mock_df.copy())
    out2 = br_default._filtrer_og_lag_aldersgrupper(out1.copy())

    key_cols = list(out1.columns)
    out1s = out1.sort_values(key_cols).reset_index(drop=True)
    out2s = out2.sort_values(key_cols).reset_index(drop=True)
    pd.testing.assert_frame_equal(out1s, out2s)


def test_normaliser_grupperingsvariabler(br_default: BirthRates) -> None:
    assert br_default._normaliser_grupperingsvariabler(None) == ["aldersgruppe"]
    assert sorted(br_default._normaliser_grupperingsvariabler("komm_nr")) == sorted(
        ["aldersgruppe", "komm_nr"]
    )
    assert sorted(
        br_default._normaliser_grupperingsvariabler(["aldersgruppe", "komm_nr"])
    ) == sorted(["aldersgruppe", "komm_nr"])
    assert sorted(
        br_default._normaliser_grupperingsvariabler(["landsdel", "utdanning"])
    ) == sorted(["aldersgruppe", "landsdel", "utdanning"])


def test_tell_per_gruppe(br_default: BirthRates) -> None:
    df = pd.DataFrame(
        {
            "alder": [25, 25, 30, 30, 30, 40],
            "kjoenn": ["2", "2", "2", "1", "1", "2"],
        }
    )

    resultat = br_default._tell_per_gruppe(df, ["alder", "kjoenn"], navn="antall")

    forventet = pd.DataFrame(
        {
            "alder": [25, 30, 30, 40],
            "kjoenn": ["2", "2", "1", "2"],
            "antall": [2, 1, 2, 1],
        }
    )

    resultat = resultat.sort_values(["alder", "kjoenn"]).reset_index(drop=True)
    forventet = forventet.sort_values(["alder", "kjoenn"]).reset_index(drop=True)

    pd.testing.assert_frame_equal(resultat, forventet, check_dtype=False)
