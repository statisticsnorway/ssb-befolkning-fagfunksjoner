import itertools
import warnings
from dataclasses import dataclass

import pandas as pd

__all__ = ["foedselsrate"]


@dataclass
class FoedselsRater:
    """Beregner fødselsrater og samlet fruktbarhetstall.

    Tar utgangspunktet i befolkningsdata ved periodens start og slutt, samt
    hendelsesdata for fødsler. Beregner middelfolkemengde per aldersgruppe
    og valgfrie grupperingsvariabler, og bruker dette som nevner i rateberegningen.

    Attributter:
        aldersgruppe_col (str): Navn på kolonnen som skal opprettes for aldersgrupper.
        alder_col (str): Navn på kolonnen med alder i inputdata.
        kjoenn_col (str): Navn på kolonnen med kjønn i inputdata.
        skala (int): Multiplikator for raten (f.eks. `1000` gir rate per 1 000).
        aldersgruppering (int): Bredde på aldersgruppene i antall år (`1` = enkeltår).
        min_alder (int): Nedre aldersgrense, inklusiv.
        maks_alder (int): Øvre aldersgrense, inklusiv.
        beregn_for_menn (bool): Hvis `True`, beregnes rater for menn (`kjoenn` = `"1"`),
            ellers beregnes rater for kvinner (`kjoenn` = `"2"`).
    """

    # Kolonnenavn
    aldersgruppe_col: str
    alder_col: str
    kjoenn_col: str

    # Konfigurasjonsparametere
    skala: int
    aldersgruppering: int
    min_alder: int
    maks_alder: int
    beregn_for_menn: bool

    def __post_init__(self) -> None:
        """Validerer konfigurasjonsparameterene etter initialisering.

        Utløser:
            ValueError: Hvis `min_alder` er større enn `maks_alder`.
            ValueError: Hvis `aldersgruppering` er større enn aldersintervallet.
            ValueError: Hvis `aldersgruppering` er mindre enn `1`.
        """
        if self.min_alder > self.maks_alder:
            raise ValueError(
                f"Ugyldig aldersintervall: 'min_alder' {self.min_alder} må være "
                f"indre enn 'maks_alder' {self.maks_alder}."
            )

        maks_mulig_bredde = (self.maks_alder - self.min_alder) + 1
        if self.aldersgruppering > maks_mulig_bredde:
            raise ValueError(
                f"Aldersgruppering ({self.aldersgruppering}) kan ikke overstige "
                f"differansen mellom min. og max. alder ({maks_mulig_bredde})."
            )

        if self.aldersgruppering < 1:
            raise ValueError("Aldersgruppering må være minst 1.")

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
                stacklevel=3,
            )

    def _normaliser_grupperingsvariabler(
        self, grupperingsvariabler: None | str | list[str]
    ) -> list[str]:
        """Normaliserer grupperingsvariabler til en liste som inkluderer `aldersgruppe_col`."""
        if grupperingsvariabler is None:
            norm_grupperingsvariabler: list[str] = []
        elif isinstance(grupperingsvariabler, str):
            norm_grupperingsvariabler = [grupperingsvariabler]
        else:
            norm_grupperingsvariabler = list(grupperingsvariabler)

        norm_grupperingsvariabler = list(set(norm_grupperingsvariabler))
        norm_grupperingsvariabler = [
            col
            for col in norm_grupperingsvariabler
            if col not in {self.aldersgruppe_col, self.alder_col}
        ]

        return [*norm_grupperingsvariabler, self.aldersgruppe_col]

    def _lag_aldersgrupper(self, alder: pd.Series) -> pd.Series:
        """Grupperer en alder-serie i aldersintervaller.

        Ved `aldersgruppering = 1` returneres alderserien med type streng uten gruppering.
        Ellers deles aldersspennet inn i like brede intervaller med bredde `aldersgruppering`,
        og med etiketter med formed `"15-19"`.

        Parametere:
            alder (pd.Series): Serie med aldre som heltall.

        Returnerer:
            Serie aldersgruppeetiketter som strenger.
        """
        if self.aldersgruppering == 1:
            return alder.astype("string")
        bins = (
            *range(self.min_alder, self.maks_alder, self.aldersgruppering),
            self.maks_alder + 1,
        )
        labels = [
            f"{min_alder}-{maks_alder - 1}"
            for min_alder, maks_alder in itertools.pairwise(bins)
        ]
        return pd.cut(
            x=alder, bins=bins, right=False, labels=labels, include_lowest=True
        ).astype("string")

    def _filtrer_og_lag_aldersgrupper(self, df: pd.DataFrame) -> pd.DataFrame:
        """Filtrerer datasettet på kjønn og alder, og lager aldersgrupper.

        Beholder kun rader for valgt kjønn og personer innenfor aldersintervallet
        `[min_alder, maks_alder]`. Deretter opprettes en ny kolonne `aldersgruppe_col`.

        Parametere:
            df: Befolknings- eller hendelsesdatasett som skal filtreres.

        Returnerer:
            Filtrert kopi av `df` med aldersgruppe-kolonne lagt til.

        Utløser:
            ValueError: Hvis `alder_col` eller ``kjoenn_col` mangler i `df`.

        Advarer:
            UserWarning: Hvis det finnes rader med manglende alder.
        """
        if self.alder_col not in df.columns:
            raise ValueError(f"Kolonnen '{self.alder_col}' finnes ikke i datasettet.")
        if self.kjoenn_col not in df.columns:
            raise ValueError(f"Kolonnen '{self.kjoenn_col}' finnes ikke i datasettet.")

        df = df.copy()

        # Filtrer på kjønn
        kjoenn = df[self.kjoenn_col].astype(str)
        df = df.loc[kjoenn.eq("1")] if self.beregn_for_menn else df.loc[kjoenn.eq("2")]

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
            & df[self.alder_col].between(self.min_alder, self.maks_alder)
        ].copy()

        # Legg til aldersgruppe kolonne
        df[self.aldersgruppe_col] = self._lag_aldersgrupper(df[self.alder_col])

        return df

    def _tell_per_gruppe(
        self, df: pd.DataFrame, grupperingsvariabler: list[str], kolonnenavn: str
    ) -> pd.DataFrame:
        """Teller antall rader per gruppe.

        Parametere:
            df: Datasettet det skal telles fra.
            grupperingsvariabler: Kolonner å gruppere etter.
            kolonnenavn: Navn på antall-kolonnen i resultatet.

        Returnerer:
            Datasett med grupperingsvariabler og antall-kolonne som heter `kolonnenavn`
        """
        return (
            df.groupby(grupperingsvariabler, dropna=False, as_index=False)
            .size()
            .rename(columns={"size": kolonnenavn})
        )

    def _beregn_middelfolkemengde(
        self,
        df_start: pd.DataFrame,
        df_slutt: pd.DataFrame,
        grupperingsvariabler: list[str],
    ) -> pd.DataFrame:
        """Beregner middelfolkemengde per aldersgruppe og grupperingsvariabler.

        Middelfolkemengden beregnes som gjennomsnittet av antall personer
        ved periodens start og slutt for hver gruppe. Begge datasett filtreres
        og aldergrupperes før opptelling.

        Parametere:
            df_start: Befolkningsdatasett ved periodens start.
            df_slutt: Befolkningsdatasett ved periodens slutt.
            grupperingsvariabler: Kolonner å gruppere etter, inkludert aldersgruppe.

        Returnerer:
            Datasett med grupperingsvariabler og kolonnene:
                `"n_df_start"`, `"n_df_slutt"`, `"middelfolkemengde"`.

        Advarer:
            UserWarning: Hvis minste gruppe har færre enn 30 observasjoner.
        """
        df_start = self._filtrer_og_lag_aldersgrupper(df_start)
        df_slutt = self._filtrer_og_lag_aldersgrupper(df_slutt)

        self._valider_grupperingsvariabler(df_start, grupperingsvariabler, "df_start")
        self._valider_grupperingsvariabler(df_slutt, grupperingsvariabler, "df_slutt")

        a = self._tell_per_gruppe(df_start, grupperingsvariabler, "n_df_start")
        b = self._tell_per_gruppe(df_slutt, grupperingsvariabler, "n_df_slutt")

        mfm = pd.merge(a, b, on=grupperingsvariabler, how="outer").fillna(0)
        mfm["middelfolkemengde"] = (mfm["n_df_start"] + mfm["n_df_slutt"]) / 2

        self._sjekk_smaa_grupper(mfm["middelfolkemengde"], 30)

        return mfm.sort_values(grupperingsvariabler).reset_index(drop=True)

    def beregn_foedselsrate(
        self,
        df_start: pd.DataFrame,
        df_slutt: pd.DataFrame,
        df_foedsler: pd.DataFrame,
        grupperingsvariabler: None | str | list[str] = None,
    ) -> pd.DataFrame:
        """Beregner fødselsrater per aldersgrupp valgte grupperingsvariabler.

        Metode:
            1. Beregn middelfolkemengde (MFM) per gruppe
            2. Tell opp fødsler per gruppe
            3. Fødselsrate = (fødsler / MFM) * `skala`

        Parametere:
            df_start (pd.DataFrame): Befolkningsdatasett ved periodens start.
            df_slutt (pd.DataFrame): Befolkningsdatasett ved periodens slutt.
            df_foedsler (pd.DataFrame): Hendelsesdatasett med fødsler.
            grupperingsvariabler (None | str | list[str]): Ekstra grupperingsvariabler utover aldersgruppe,
                f.eks. `"landsdel"` eller `["komm_nr", "invkat"]`.
                `None` gir kun gruppering på aldersgruppe.

        Returnerer:
            Et datasett med fødselsrater:
                - `grupperingsvariabler`
                - `"n_df_start"`
                - `"n_df_slutt"`
                - `"middelfolkemengde"`
                - `"n_foedsler"`
                - `"foedselsrate"`

        Advarer:
            UserWarning: Hvis minste gruppe har færre enn 10 fødsler.
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
    ) -> float:
        """Beregner samlet fruktbarhetstall.

        Metode:
            1. Beregn aldersgruppert fruktbarhetsrater
            2. Summer over aldersgrupper

        Parametere:
            df_start (pd.DataFrame): Befolkningsdatasett ved periodens start.
            df_slutt (pd.DataFrame): Befolkningsdatasett ved periodens slutt.
            df_foedsler (pd.DataFrame): Hendelsesdatasett med fødsler.
            grupperingsvariabler (None | str | list[str]): Variabler å gruppere rater på utover aldersgruppe,
                f.eks. `"landsdel"` eller `["komm_nr", "invkat"]`.
                `None` gir kun gruppering på aldersgruppe.

        Returnerer:
            Samlet fruktbarhetstall som `float`.
        """
        foedselsrater = self.beregn_foedselsrate(
            df_start, df_slutt, df_foedsler, grupperingsvariabler
        )
        return float(foedselsrater["foedselsrate"].sum())


# ------------------------------------------------------------------------
# Wrappers
# ------------------------------------------------------------------------


def foedselsrate(
    df_start: pd.DataFrame,
    df_slutt: pd.DataFrame,
    df_foedsler: pd.DataFrame,
    *,
    grupperingsvariabler: None | str | list[str] = None,
    aldersgruppe_col: str = "aldersgruppe",
    alder_col: str = "alder",
    kjoenn_col: str = "kjoenn",
    skala: int = 1000,
    aldersgruppering: int = 1,
    min_alder: int = 15,
    maks_alder: int = 49,
    beregn_for_menn: bool = False,
) -> pd.DataFrame:
    """Beregner fødselsrater per aldersgruppe og valgfrie grupperingsvariabler.

    Parametere:
        df_start (pd.DataFrame): Befolkningsdatasett ved periodens start.
            Må inneholde alder- og grupperingskolonner.
        df_slutt (pd.DataFrame): Befolkningsdatasett ved periodens slutt.
            Må inneholde alder- og grupperingskolonner.
        df_foedsler (pd.DataFrame): Hendelsesdatasett med fødsler.
        grupperingsvariabler (None | str | list[str]): Variabler å gruppere rater på utover aldersgruppe,
            f.eks. `"landsdel"` eller `["komm_nr", "invkat"]`.
            `None` gir kun gruppering på aldersgruppe.
        aldersgruppe_col (str): Navn på kolonnen som skal opprettes for aldersgrupper.
            Default er `aldersgruppe`.
        alder_col (str): Navn på kolonnen med alder i inputdata. Default er `alder`
        kjoenn_col (str): Navn på kolonnen med kjønn i inputdata. Default er `kjoenn`
        skala (int): Multiplikator for raten. Default er `1000` (rate per 1 000).
        aldersgruppering (int): Bredde på aldersgruppene i antall år. Default er `1` (enkeltår).
        min_alder (int): Nedre aldersgrense, inklusiv. Default er `15`.
        maks_alder (int): Øvre aldersgrense, inklusiv. Default er `49`.
        beregn_for_menn (bool): Hvis `True`, beregnes rater for menn (`kjoenn` = `"1"`),
            ellers beregnes rater for kvinner (`kjoenn` = `"2"`).
            Default er `False`.

    Returnerer:
        Et datasett med fødselsrater:
            - `grupperingsvariabler`
            - `"n_df_start"`
            - `"n_df_slutt"`
            - `"middelfolkemengde"`
            - `"n_foedsler"`
            - `"foedselsrate"`

    Eksempler:
    >>> import pandas as pd

    >>> # Befolkning ved periodens start
    >>> df_start = pd.DataFrame({
    ...     "alder": [20, 21, 22, 30, 31],
    ...     "kjoenn": ["2", "2", "2", "2", "2"],
    ...     "fylke": ["01", "03", "03", "39", "55"],
    ... })

    >>> # Befolkning ved periodens slutt
    >>> df_slutt = pd.DataFrame({
    ...     "alder": [20, 21, 22, 30, 31],
    ...     "kjoenn": ["2", "2", "2", "2", "2"],
    ...     "fylke": ["01", "03", "03", "39", "55"],
    ... })

    >>> # Fødsler i perioden
    >>> df_foedsler = pd.DataFrame({
    ...     "alder": [20, 21, 30],
    ...     "kjoenn": ["2", "2", "2"],
    ...     "fylke": ["03", "03", "39"],
    ... })

    >>> # Med 5-årsgrupper
    >>> foedselsrate(df_start, df_slutt, foedsler, aldersgruppering=5)

    >>> # Gruppert etter fylke
    >>> foedselsrate(df_start, df_slutt, foedsler, grupperingsvariabler="fylke")
    """
    foedselsrater = FoedselsRater(
        aldersgruppe_col=aldersgruppe_col,
        alder_col=alder_col,
        kjoenn_col=kjoenn_col,
        skala=skala,
        aldersgruppering=aldersgruppering,
        min_alder=min_alder,
        maks_alder=maks_alder,
        beregn_for_menn=beregn_for_menn,
    )

    return foedselsrater.beregn_foedselsrate(
        df_start, df_slutt, df_foedsler, grupperingsvariabler
    )


def samlet_fruktbarhet(
    df_start: pd.DataFrame,
    df_slutt: pd.DataFrame,
    df_foedsler: pd.DataFrame,
    *,
    grupperingsvariabler: None | str | list[str] = None,
    aldersgruppe_col: str = "aldersgruppe",
    alder_col: str = "alder",
    kjoenn_col: str = "kjoenn",
    skala: int = 1000,
    aldersgruppering: int = 1,
    min_alder: int = 15,
    maks_alder: int = 49,
    beregn_for_menn: bool = False,
) -> float:
    """Beregner samlet fruktbarhetstall per 1000 etter aldersgrupper.

    Parametere:
        df_start (pd.DataFrame): Befolkningsdatasett ved periodens start.
            Må inneholde alder- og grupperingskolonner.
        df_slutt (pd.DataFrame): Befolkningsdatasett ved periodens slutt.
            Må inneholde alder- og grupperingskolonner.
        df_foedsler (pd.DataFrame): Hendelsesdatasett med fødsler.
        grupperingsvariabler (None | str | list[str]): Variabler å gruppere rater på utover aldersgruppe,
            f.eks. `"landsdel"` eller `["komm_nr", "invkat"]`.
            `None` gir kun gruppering på aldersgruppe.
        aldersgruppe_col (str): Navn på kolonnen som skal opprettes for aldersgrupper.
            Default er `aldersgruppe`.
        alder_col (str): Navn på kolonnen med alder i inputdata. Default er `alder`
        kjoenn_col (str): Navn på kolonnen med kjønn i inputdata. Default er `kjoenn`
        skala (int): Multiplikator for raten. Default er `1000` (rate per 1 000).
        aldersgruppering (int): Bredde på aldersgruppene i antall år. Default er `1` (enkeltår).
        min_alder (int): Nedre aldersgrense, inklusiv. Default er `15`.
        maks_alder (int): Øvre aldersgrense, inklusiv. Default er `49`.
        beregn_for_menn (bool): Hvis `True`, beregnes rater for menn (`kjoenn` = `"1"`),
            ellers beregnes rater for kvinner (`kjoenn` = `"2"`).
            Default er `False`.

    Returnerer:
        Samlet fruktbarhetstall som `float`.

    Eksempler:
    >>> import pandas as pd

    >>> # Befolkning ved periodens start
    >>> df_start = pd.DataFrame({
    ...     "alder": [20, 21, 22, 30, 31],
    ...     "kjoenn": ["2", "2", "2", "2", "2"],
    ...     "fylke": ["01", "03", "03", "39", "55"],
    ... })

    >>> # Befolkning ved periodens slutt
    >>> df_slutt = pd.DataFrame({
    ...     "alder": [20, 21, 22, 30, 31],
    ...     "kjoenn": ["2", "2", "2", "2", "2"],
    ...     "fylke": ["01", "03", "03", "39", "55"],
    ... })

    >>> # Fødsler i perioden
    >>> df_foedsler = pd.DataFrame({
    ...     "alder": [20, 21, 30],
    ...     "kjoenn": ["2", "2", "2"],
    ...     "fylke": ["03", "03", "39"],
    ... })

    >>> # Med 5-årsgrupper
    >>> foedselsrate(df_start, df_slutt, df_foedsler, aldersgruppering=5)

    >>> # Gruppert etter fylke
    >>> foedselsrate(df_start, df_slutt, df_foedsler, grupperingsvariabler="fylke")
    """
    foedselsrater = FoedselsRater(
        aldersgruppe_col=aldersgruppe_col,
        alder_col=alder_col,
        kjoenn_col=kjoenn_col,
        skala=skala,
        aldersgruppering=aldersgruppering,
        min_alder=min_alder,
        maks_alder=maks_alder,
        beregn_for_menn=beregn_for_menn,
    )

    return foedselsrater.beregn_samlet_fruktbarhetstall(
        df_start, df_slutt, df_foedsler, grupperingsvariabler
    )


# ------------------------------------------------------------------------
# Nice to have:
# 1. Confidence intervals (poisson?)
# 2. Visualisation
# ------------------------------------------------------------------------
