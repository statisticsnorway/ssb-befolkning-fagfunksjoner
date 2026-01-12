import itertools
import warnings
from dataclasses import dataclass
from typing import cast

import pandas as pd

__all__ = ["foedselsrate"]


@dataclass
class BirthRates:
    # Init kolonnenavn
    aldersgruppe_col: str
    alder_col: str
    kjoenn_col: str

    # Init konfig parametre
    skala: int
    aldersgruppering: int
    min_alder: int
    max_alder: int
    beregn_for_menn: bool

    @staticmethod
    def _valider_grupperingsvariabler(
        df: pd.DataFrame, grupperingsvariabler: list[str], navn_df: str
    ) -> None:
        """Sjekker at alle grupperingsvariabler finnes i datasettet."""
        mangler = [col for col in grupperingsvariabler if col not in df.columns]
        if mangler:
            raise ValueError(
                f"Datasett '{navn_df}' mangler grupperingskolonner: {mangler}."
            )

    def _sjekk_smaa_grupper(self, gruppert_antall: pd.Series, terskel: int) -> None:
        """Gir advarsel dersom minste gruppe har færre observasjoner enn terskelverdien."""
        if gruppert_antall.empty:
            return

        min_n = gruppert_antall.min()
        if min_n < terskel:
            warnings.warn(
                f"Minste gruppe har n={min_n}. "
                f"Vurder å øke aldersgruppering fra {self.aldersgruppering} "
                "eller aggregere grupperingsvariabler.",
                stacklevel=1,
            )

    def _normaliser_grupperingsvariabler(
        self, grupperingsvariabler: None | str | list[str]
    ) -> list[str]:
        """Konverterer grupperingsvariabler til en liste som alltid inkluderer aldersgruppen."""
        if grupperingsvariabler is None:
            norm_grupperingsvariabler: list[str] = []
        elif isinstance(grupperingsvariabler, str):
            norm_grupperingsvariabler = [grupperingsvariabler]
        else:
            norm_grupperingsvariabler = list(grupperingsvariabler)

        norm_grupperingsvariabler = [
            col for col in norm_grupperingsvariabler if col != self.aldersgruppe_col
        ]

        return [*norm_grupperingsvariabler, self.aldersgruppe_col]

    def _lag_aldersgrupper(self, alder: pd.Series) -> pd.Series:
        """Lager aldersgrupper av kolonne med aldre.

        Validerer at parameterverdiene er fornuftige, og sikrer at øvre grense
        i siste aldersbånd ikke går over max_alder.
        """
        # Valider parametre
        if self.min_alder > self.max_alder:
            raise ValueError(
                f"Ugyldig aldersintervall: 'min_alder' {self.min_alder} må være mindre enn 'max_alder' {self.max_alder}."
            )

        maks_mulig_bredde = (self.max_alder - self.min_alder) + 1
        if self.aldersgruppering > maks_mulig_bredde:
            raise ValueError(
                f"Aldersgruppering ({self.aldersgruppering}) kan ikke overstige alderområdet ({maks_mulig_bredde})."
            )

        if self.aldersgruppering < 1:
            raise ValueError("Aldersgruppering må være minst 1.")

        if self.aldersgruppering == 1:
            return alder.astype("string")

        bins = (
            *range(self.min_alder, self.max_alder, self.aldersgruppering),
            self.max_alder + 1,
        )
        labels = [
            f"{min_alder}-{max_alder - 1}"
            for min_alder, max_alder in itertools.pairwise(bins)
        ]

        return pd.cut(
            x=alder, bins=bins, right=False, labels=labels, include_lowest=True
        ).astype("string")

    def _filtrer_og_lag_aldersgrupper(
        self,
        df: pd.DataFrame,
    ) -> pd.DataFrame:
        """Filtrerer datasettet på kjønn og alder, og lager aldersgrupper.

        Datasettet filtreres til valgt kjønn og til personer innenfor aldersintervallet: 'min_alder' til 'max_alder'.
        Deretter opprettes en ny kolonne med aldersgrupper basert på 'aldersgruppering'.
        """
        # Validerer parametre
        if self.alder_col not in df.columns:
            raise ValueError(f"Kolonnen '{self.alder_col}' finnes ikke i datasettet.")
        if self.kjoenn_col not in df.columns:
            raise ValueError(f"Kolonnen '{self.kjoenn_col}' finnes ikke i datasettet.")

        # Lokal kopi
        df = df.copy()

        # Filtrer på kjønn
        kj = df[self.kjoenn_col].astype(str)
        df = df.loc[kj.eq("1")] if self.beregn_for_menn else df.loc[kj.eq("2")]

        # Filtrer på alder
        df[self.alder_col] = df[self.alder_col].astype("Int64")
        n_missing_alder = df[self.alder_col].isna().sum()
        if n_missing_alder > 0:
            warnings.warn(
                f"Fant {n_missing_alder} rader med manglende alder. "
                f"Disse ekskluderes fra beregningen.",
                stacklevel=1,
            )
        df = df.loc[
            df[self.alder_col].notnull()
            & df[self.alder_col].between(self.min_alder, self.max_alder)
        ].copy()

        # Legg til aldersgruppe kolonne
        df[self.aldersgruppe_col] = self._lag_aldersgrupper(df[self.alder_col])

        return df

    def _tell_per_gruppe(
        self, df: pd.DataFrame, grupperingsvariabler: list[str], navn: str
    ) -> pd.DataFrame:
        """Teller rader per gruppe."""
        return (
            df.groupby(grupperingsvariabler, dropna=False, as_index=False)
            .size()
            .rename(columns={"size": navn})
        )

    def _beregn_middelfolkemengde(
        self,
        df_start: pd.DataFrame,
        df_slutt: pd.DataFrame,
        grupperingsvariabler: list[str],
    ) -> pd.DataFrame:
        """Beregner middelfolkemengde gruppert etter alder og valgte grupperingsvaraiabler.

        Middelfolkemengden beregnes som gjennomsnittet av antall personer
        ved periodens start og slutt, for hver gruppe.
        """
        # Prepp datasett
        df_start = self._filtrer_og_lag_aldersgrupper(df_start)
        df_slutt = self._filtrer_og_lag_aldersgrupper(df_slutt)

        # Valider at grupperingskolonner finnes i datasettene
        self._valider_grupperingsvariabler(df_start, grupperingsvariabler, "df_start")
        self._valider_grupperingsvariabler(df_slutt, grupperingsvariabler, "df_slutt")

        # Tell opp antall personer per gruppe
        a = self._tell_per_gruppe(df_start, grupperingsvariabler, "n_df_start")
        b = self._tell_per_gruppe(df_slutt, grupperingsvariabler, "n_df_slutt")

        # Beregner middelfolkemengde per gruppe
        mfm = pd.merge(a, b, on=grupperingsvariabler, how="outer").fillna(0)
        mfm["middelfolkemengde"] = (mfm["n_df_start"] + mfm["n_df_slutt"]) / 2

        # Sjekk for små grupper
        self._sjekk_smaa_grupper(mfm["middelfolkemengde"], 30)

        return mfm.sort_values(grupperingsvariabler).reset_index(drop=True)

    def beregn_foedselsrate(
        self,
        df_start: pd.DataFrame,
        df_slutt: pd.DataFrame,
        df_foedsler: pd.DataFrame,
        grupperingsvariabler: None | str | list[str] = None,
    ) -> pd.DataFrame:
        """Beregner fødselsrater per 1000 etter aldersgrupper og valgte grupperingsvariabler.

        Metode:
        1) Beregn middelfolkemengde (MFM) per gruppe
        2) Tell opp fødsler per gruppe
        3) Fødselsrate = (fødsler / MFM) * 1000

        Parametere
        ----------
        df_start : pd.DataFrame
            Befolkning ved periodens start.
        df_slutt : pd.DataFrame
            Befolkning ved periodens slutt.
        df_foedsler : pd.DataFrame
            Hendelsesdata for fødsler.
        grupperingsvariabler : None | str | list[str]
            Ekstra grupperingsvariabler i tillegg til aldersgruppe (f.eks. "landsdel", ["kommnr", "innvkat"]).

        Returnerer
        ----------
        pd.DataFrame
            Tabell med kolonnene:
            grupperingsvariabler + ["n_df_start", "n_df_slutt", "middelfolkemengde", "n_foedsler", "foedselsrate"].
        """
        # Normaliser grupperingsvariabler til list[str]
        grupperingsvariabler = self._normaliser_grupperingsvariabler(
            grupperingsvariabler
        )

        # Lager middelfolkemengde
        mfm = self._beregn_middelfolkemengde(df_start, df_slutt, grupperingsvariabler)

        # Tell opp fødsler per gruppe
        df_foedsler = self._filtrer_og_lag_aldersgrupper(df_foedsler)
        self._valider_grupperingsvariabler(
            df_foedsler, grupperingsvariabler, "df_foedsler"
        )

        antall_foedsler = (
            df_foedsler.groupby(grupperingsvariabler, dropna=False, as_index=False)
            .size()
            .rename(columns={"size": "n_foedsler"})
        )

        # Sjekk etter små grupper
        self._sjekk_smaa_grupper(antall_foedsler["n_foedsler"], terskel=10)

        # Slå sammen og beregn fødselsrate
        df_foedselsrater = mfm.merge(
            antall_foedsler, how="left", on=grupperingsvariabler
        )
        df_foedselsrater["foedselsrate"] = (
            df_foedselsrater["n_foedsler"] / df_foedselsrater["middelfolkemengde"]
        ) * self.skala

        return df_foedselsrater.sort_values(grupperingsvariabler).reset_index(drop=True)

    def beregn_samlet_fruktbarhetstall(
        self,
        df_start: pd.DataFrame,
        df_slutt: pd.DataFrame,
        df_foedsler: pd.DataFrame,
        grupperingsvariabler: str | list[str] | None = None,
    ) -> int:
        """Regner ut samlet fruktbarhetstall etter aldersgrupper med mulighet for å gruppere etter valgt grupperingsvariabel.

        Samlet fruktbarhetstall er summen av fødselsrater.
        """
        foedselsrater = self.beregn_foedselsrate(
            df_start, df_slutt, df_foedsler, grupperingsvariabler
        )
        samlet_fruktbarhet = cast(int, foedselsrater["foedselsrate"].sum())

        return samlet_fruktbarhet


def foedselsrate(
    df_start: pd.DataFrame,
    df_slutt: pd.DataFrame,
    df_foedsler: pd.DataFrame,
    grupperingsvariabler: None | str | list[str],
    *,
    aldersgruppe_col: str = "aldersgruppe",
    alder_col: str = "alder",
    kjoenn_col: str = "kjoenn",
    skala: int = 1000,
    aldersgruppering: int = 1,
    min_alder: int = 15,
    max_alder: int = 49,
    beregn_for_menn: bool = False,
) -> pd.DataFrame:
    """Function for calculating the birth rate."""
    foedselsrater = BirthRates(
        aldersgruppe_col=aldersgruppe_col,
        alder_col=alder_col,
        kjoenn_col=kjoenn_col,
        skala=skala,
        aldersgruppering=aldersgruppering,
        min_alder=min_alder,
        max_alder=max_alder,
        beregn_for_menn=beregn_for_menn,
    )

    return foedselsrater.beregn_foedselsrate(
        df_start, df_slutt, df_foedsler, grupperingsvariabler
    )
