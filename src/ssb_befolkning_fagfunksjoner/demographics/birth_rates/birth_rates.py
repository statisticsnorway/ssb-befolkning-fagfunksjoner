import pandas as pd
import numpy as np


# ------------------------------------------------------------------------
# Main functions
# ------------------------------------------------------------------------

def beregn_foedselsrate(
    df_start: pd.DataFrame,
    df_slutt: pd.DataFrame,
    df_foedsler: pd.DataFrame,
    *,
    aldersgruppering: int = 1,
    grupperingsvariabler: str | list[str] | None = None,
    aldersgruppe_col: str = "aldersgruppe",
    alder_col: str = "alder",
    kjoenn_col: str = "kjoenn",
):
    """
    Regner ut fødselsrater etter aldersgrupper med mulighet for å gruppere etter valgt grupperingsvariabel.

    Fødselsraten er antall fødsler i forhold til middelfolkemengden i en gitt periode.

    Rå fødselsrate = (antall fødsler i perioden) / (middelfolkemengde) * 1000
    Aldersspesifikk fødselsrate = (antall fødsler for kvinner i alder x) / (middelfolkemengde for alder x) * 1000
    """
    pass



def beregn_samlet_fruktbarhetstall(
    df_start: pd.DataFrame,
    df_slutt: pd.DataFrame,
    df_foedsler: pd.DataFrame,
    *,
    aldersgruppering: int = 1,
    grupperingsvariabler: str | list[str] | None = None,
    aldersgruppe_col: str = "aldersgruppe",
    alder_col: str = "alder",
    kjoenn_col: str = "kjoenn",
):
    """
    Regner ut samlet fruktbarhetstall etter aldersgrupper med mulighet for å gruppere etter valgt grupperingsvariabel.

    Samlet fruktbarhetstall er summen av fødselsrater.
    """
    pass


# ------------------------------------------------------------------------
# Helper functions
# ------------------------------------------------------------------------

def _norm_group_by_cols(
    group_by: list[str] | str | None, 
    aldersgruppe_col: str,
) -> list[str]:
    """Normaliserer grupperingsvariabler, inkluderer alltid aldersgruppe_col."""
    if group_by is None:
        grupperingsvariabler: list[str] = []
    elif isinstance(group_by, str):
        grupperingsvariabler = [group_by]
    else:
        grupperingsvariabler = list(group_by)
    
    grupperingsvariabler = [col for col in grupperingsvariabler if col != aldersgruppe_col]

    return [*grupperingsvariabler, aldersgruppe_col]


def _valider_grupperingsvariabler(
    df: pd.DataFrame,
    grupperingsvariabler: list[str], navn_df: str
) -> None:
    mangler = [col for col in grupperingsvariabler if col not in df.columns]
    if mangler:
        raise ValueError(f"Datasett '{navn_df}' mangler grupperingskolonner: {mangler}.")


def _beregn_middelfolkemengde(
    df_start: pd.DataFrame,
    df_slutt: pd.DataFrame,
    aldersgruppering: int,
    aldersgruppe_col: str,
    alder_col: str,
    kjoenn_col: str,
    *,
    grupperingsvariabler: None | str | list[str] = None,
) -> pd.DataFrame:
    """Beregner middelfolkemengde, gruppert på aldersgruppe og gitte grupperingsvariabler."""
    df_start = _prep_folketall(
        df_start,
        aldersgruppering,
        aldersgruppe_col,
        alder_col,
        kjoenn_col
    )
    df_slutt = _prep_folketall(
        df_slutt,
        aldersgruppering,
        aldersgruppe_col,
        alder_col,
        kjoenn_col,
    )

    # Normaliser grupperingsvariabler
    grupperingsvariabler = _norm_group_by_cols(grupperingsvariabler, aldersgruppe_col)

    # Valider at grupperingskolonner finnes i datasettene
    _valider_grupperingsvariabler(df_start, grupperingsvariabler, "df_start")
    _valider_grupperingsvariabler(df_slutt, grupperingsvariabler, "df_slutt")

    # Tell opp antall personer per gruppe
    a = df_start.groupby(grupperingsvariabler, dropna=False).size().rename("n_df_start")
    b = df_slutt.groupby(grupperingsvariabler, dropna=False).size().rename("n_df_slutt")

    # Beregner middelfolkemengde per gruppe
    mfm = pd.concat([a, b], axis=1).fillna(0)
    mfm["middelfolkemengde"] = (mfm["n_df_start"] + mfm["n_df_slutt"]) / 2

    return mfm.reset_index()


def _prep_folketall(
    df: pd.DataFrame,
    aldersgruppering: int,
    aldersgruppe_col: str,
    alder_col: str,
    kjoenn_col: str,
    min_alder: int = 15,
    max_alder: int = 49,
) -> pd.DataFrame:
    """
    Filtrerer folketall til kun kvinner mellom 'min_alder' og 'max_alder', og lager aldersgrupper.
    
    Standard 'min_alder' = 15, og 'max_alder' = 49
    """
    # Valider parametre
    if alder_col not in df.columns:
        raise ValueError(f"Kolonnen '{alder_col}' finnes ikke i datasettet.")
    
    if kjoenn_col not in df.columns:
        raise ValueError(f"Kolonnen '{kjoenn_col}' finnes ikke i datasettet.")

    if aldersgruppering < 1:
        raise ValueError("Parameteret 'aldersgruppering' må være minst 1.")

    # Filtrer på kjoenn
    df = df.loc[df[kjoenn_col] == "2"].copy()

    # Filtrer på alder
    df = df.loc[
        (df[alder_col] >= min_alder)
        & (df[alder_col] <= max_alder)
    ].copy()

    # Beregn nedre og øvre grense for hver aldersgruppe 
    nedre = ((df[alder_col] - min_alder) // aldersgruppering) * aldersgruppering + min_alder
    oevre = nedre + aldersgruppering - 1

    # Lag aldersgruppe kolonne
    df[aldersgruppe_col] = np.where(
        aldersgruppering == 1,
        nedre.astype(str),  # Hvis aldersgruppering er = 1 bruk alder som aldersgruppe
        nedre.astype(str) + "-" + oevre.astype(str)
    )

    return df


# ------------------------------------------------------------------------
# Testing the functions
# ------------------------------------------------------------------------

df_start = pd.read_parquet("/buckets/produkt/bosatte/klargjorte-data/2024/bosatte_p2024-12-31.parquet")
df_slutt = pd.read_parquet("/buckets/produkt/bosatte/klargjorte-data/2025/bosatte_p2025-01-01.parquet")

# Hvordan funker _beregn_middelfolkemengde()

# Steg 1: prepp folketall data
df_start = _prep_folketall(
    df=df_start,
    aldersgruppering = 5,
    aldersgruppe_col="aldersgruppe",
    alder_col="alderu",
    kjoenn_col="kjoenn"
)

df_slutt = _prep_folketall(
    df=df_slutt,
    aldersgruppering = 5,
    aldersgruppe_col="aldersgruppe",
    alder_col="alderu",
    kjoenn_col="kjoenn"
)
df_start

# Steg 2: normalisere grupperingsvariabler
grupperingsvariabler_0 = None 
norm_0 = _norm_group_by_cols(grupperingsvariabler_0, aldersgruppe_col="aldersgruppe")
norm_0

grupperingsvariabler_1 = "komm_nr"
norm_1 = _norm_group_by_cols(grupperingsvariabler_1, aldersgruppe_col="aldersgruppe")
norm_1

grupperingsvariabler_2 = ["sivilstand", "landkode"]
norm_2 = _norm_group_by_cols(grupperingsvariabler_2, aldersgruppe_col="aldersgruppe")
norm_2


# Steg 3: validere at kolonnene finnes
_valider_grupperingsvariabler(df_start, norm_1, "df_start")
_valider_grupperingsvariabler(df_start, norm_2, "df_start")  # skal feile fordi landkode ikke finnes

# Steg 4: tell opp antall personer per gruppe
a = df_start.groupby(norm_1, dropna=False).size().rename("n_df_start")
a
b = df_slutt.groupby(norm_1, dropna=False).size().rename("n_df_slutt")
b

# Steg 5: beregn mfm
mfm = pd.concat([a, b], axis=1).fillna(0)
mfm["middelfolkemengde"] = (mfm["n_df_start"] + mfm["n_df_slutt"]) / 2
mfm.reset_index()

# I alt
mfm = _beregn_middelfolkemengde(
    df_start,
    df_slutt,
    5,
    "aldersgruppe",
    "alderu",
    "kjoenn",
)
mfm
