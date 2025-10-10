import logging

import pandas as pd
from tabulate import tabulate

logger = logging.getLogger(__name__)


def dublettsjekk(
    inndata: pd.DataFrame | pd.Series, variabler: list[str] | None = None
) -> pd.DataFrame:
    """Utfører en dublettsjekk på and pandas DataFrame eller Series.

    Funksjonen:
    - Printer antall unike verdier som forekommer to eller flere ganger.
    - Printer hvor mange rader disse verdiene fordeler seg på.
    - Returnerer en frekvenstabell med hvilke verdier det gjelder, antall forekomster.
    - Sammenligner antall rader i parameter1 og parameter2 og printer differansen.

    Parametre:
    - inndata (pd.DataFrame | pd.Series): Et datasett eller en serie som skal sjekkes for dubletter
    - variabler (list[str]): Liste med variabler som skal sjekkes for dubletter, dersom inndata er DataFrame

    Eksempel:

    """
    dub_frekvens = _dublett_frekvens_pandas(inndata, variabler)
    _log_dublett_frekvens(dub_frekvens)

    return dub_frekvens


def _dublett_frekvens_pandas(
    inndata: pd.DataFrame | pd.Series, variabler: list[str] | str | None = None
) -> pd.DataFrame:
    """Beregner frekvenstabell for dubletter i en pandas Series eller DataFrame."""
    # Tell opp dubletter for Series
    if isinstance(inndata, pd.Series):
        if isinstance(variabler, list | str):
            raise ValueError("Forventer ikke 'variabler' sammen med en serie.")
        return (
            inndata[inndata.duplicated(keep=False)]
            .value_counts(ascending=False)
            .reset_index(name="antall")
        )

    # Tell opp dubletter for DataFrame
    if isinstance(inndata, pd.DataFrame):
        if variabler is None:
            variabler = inndata.columns.tolist()

        # Validering av variabelnavn i DataFrame
        missing = [v for v in variabler if v not in inndata.columns]
        if missing:
            raise ValueError(f"Variabler {missing} finnes ikke i DataFrame.")

        return (
            inndata[inndata.duplicated(subset=variabler, keep=False)]
            .value_counts(ascending=False)
            .reset_index(name="antall")
        )


def _log_dublett_frekvens(count: pd.DataFrame) -> None:
    """Log how many duplicated rows and show distribution table."""
    logger.info(f"Antall dublett-verdier = {count['antall'].sum()}")
    logger.info(f"Antall rader med dubletter = {len(count)}")

    if count["antall"].sum() == 0:
        return

    freq_table = tabulate(
        count.to_records(index=False),
        headers="keys",
        tablefmt="pretty",
        showindex=False,
    )

    logger.info("Frekvenstabell for dubletter:\n" + freq_table)
