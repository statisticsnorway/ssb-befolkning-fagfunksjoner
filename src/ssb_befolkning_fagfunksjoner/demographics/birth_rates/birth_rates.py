from dataclasses import dataclass
import pandas as pd
import numpy as np


@dataclass
class BirthRates:
    # Init kolonnenavn
    aldersgruppe_col: str
    alder_col: str
    kjoenn_col: str

    # Init konfig parametre
    aldersgruppering: int
    min_alder: int
    max_alder: int
    beregn_for_menn: bool


    def beregn_middelfolkemngde(
        self,
        df_start: pd.DataFrame,
        df_slutt: pd.DataFrame,
        grupperingsvariabler: None | str | list[str]
    ) -> pd.DataFrame:
        """Beregner middelfolkemengde, gruppert på aldersgruppe og utvalgte grupperingsvariabler."""
        # Normaliser grupperingsvariabler
        grupperingsvariabler = self._normaliser_grupperingsvariabler(grupperingsvariabler)

        df_start = self._prep_folketall(df_start)
        df_slutt = self._prep_folketall(df_slutt)

        # Valider at grupperingskolonner finnes i datasettene
        self._valider_grupperingsvariabler(df_start, grupperingsvariabler, "df_start")
        self._valider_grupperingsvariabler(df_slutt, grupperingsvariabler, "df_slutt")

        # Tell opp antall personer per gruppe
        a = df_start.groupby(grupperingsvariabler, dropna=False).size().rename("n_df_start")
        b = df_slutt.groupby(grupperingsvariabler, dropna=False).size().rename("n_df_slutt")

        # Beregner middelfolkemengde per gruppe
        mfm = pd.concat([a, b], axis=1).fillna(0)
        mfm["middelfolkemengde"] = (mfm["n_df_start"] + mfm["n_df_slutt"]) / 2

        return mfm.reset_index()

    @staticmethod
    def _valider_grupperingsvariabler(
        df: pd.DataFrame,
        grupperingsvariabler: list[str],
        navn_df: str
    ) -> None:
        mangler = [col for col in grupperingsvariabler if col not in df.columns]
        if mangler:
            raise ValueError(f"Datasett '{navn_df}' mangler grupperingskolonner: {mangler}.")


    def _normaliser_grupperingsvariabler(
        self,
        grupperingsvariabler: None | str | list[str]
    ) -> list[str]:
        """Normaliserer grupperingsvariabler, inkluderer alltid aldersgruppe_col."""
        if grupperingsvariabler is None:
            norm_grupperingsvariabler: list[str] = []
        elif isinstance(grupperingsvariabler, str):
            norm_grupperingsvariabler = [grupperingsvariabler]
        else:
            norm_grupperingsvariabler = list(grupperingsvariabler)
        
        norm_grupperingsvariabler = [col for col in norm_grupperingsvariabler if col != self.aldersgruppe_col]

        return [*norm_grupperingsvariabler, self.aldersgruppe_col]


    def _prep_folketall(
        self,
        df: pd.DataFrame,
    ) -> pd.DataFrame:
        """Filtrerer folketall til kun kvinner (med mindre beregn_for_menn er satt til True), mellom 'min_alder' og 'max_alder', og lager aldersgrupper."""
        # Validerer parametre
        if self.alder_col not in df.columns:
            raise ValueError(f"Kolonnen '{self.alder_col}' finnes ikke i datasettet.")

        if self.kjoenn_col not in df.columns:
            raise ValueError(f"Kolonnen '{self.kjoenn_col}' finnes ikke i datasettet.")

        if self.aldersgruppering < 1:
            raise ValueError("Parameteret 'aldersgruppering' må være minst 1.")

        # Filtrer på kjoenn
        if self.beregn_for_menn:
            df = df.loc[df[self.kjoenn_col] == "1"].copy()
        else:
            df = df.loc[df[self.kjoenn_col] == "2"].copy()

        # Filtrer på alder
        df = df.loc[(df[self.alder_col] >= self.min_alder) & (df[self.alder_col] <= self.max_alder)].copy()

        # Beregn nedre og øvre grense for hver aldersgruppe
        lower = ((df[self.alder_col] - self.min_alder) // self.aldersgruppering) * self.aldersgruppering + self.min_alder
        upper = lower + self.aldersgruppering - 1

        # Lag aldersgruppe kolonne
        df[self.aldersgruppe_col] = np.where(
            self.aldersgruppering == 1,
            lower.astype(str),  # Hvis aldersgruppering = 1, bruk alder som aldersgruppe
            lower.astype(str) + "-" + upper.astype(str)
        )

        return df


# -----------------------------------------------------
# Main functions
# -----------------------------------------------------

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
# Testing the functions
# ------------------------------------------------------------------------

df_start = pd.read_parquet("/buckets/produkt/bosatte/klargjorte-data/2024/bosatte_p2024-01-01.parquet")
df_slutt = pd.read_parquet("/buckets/produkt/bosatte/klargjorte-data/2024/bosatte_p2024-12-31.parquet")

# Hvordan funker _beregn_middelfolkemengde()

# Steg 1: prepp folketall data
df_start = _prep_folketall(
    df=df_start,
    aldersgruppering = 5,
    aldersgruppe_col="aldersgruppe",
    alder_col="alder",
    kjoenn_col="kjoenn"
)

df_slutt = _prep_folketall(
    df=df_slutt,
    aldersgruppering = 5,
    aldersgruppe_col="aldersgruppe",
    alder_col="alder",
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
    "alder",
    "kjoenn",
)
mfm

# -------------------------------------------------------------------
# Class examples
# -------------------------------------------------------------------

# at the bottom of script
# birthrates = BirthRates()

# how to use 
# from ssb_befolkning_fagfunksjoner import birthrates
# birthrates.beregn...

# from ssb_befolkning_fagfunksjoner import BirthRates
# birthrates = BirthRates()
# birthrates.beregn...
