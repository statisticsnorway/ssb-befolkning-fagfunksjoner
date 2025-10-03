import pandas as pd


def dublettsjekk(inndata: pd.DataFrame | pd.Series, variabler: list[str] | None = None):
    """
    Utfører en dublettsjekk på and pandas DataFrame eller Series.

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

    if isinstance(inndata, pd.DataFrame):
        alle_dub = inndata[inndata.duplicated(subset=variabler, keep=False)]
        dub_frekvens = alle_dub.groupby(variabler).size().reset_index(name="antall")
        dub_frekvens = dub_frekvens.sort_values(by="antall", ascending=False).reset_index(drop=True)

    if isinstance(inndata, pd.Series):
        mask = inndata.duplicated(keep=False)
        alle_dub = inndata[mask]
        dub_frekvens = alle_dub.value_counts(ascending=False)
        dub_frekvens = dub_frekvens.reset_index()
        dub_frekvens.rename(columns={dub_frekvens.columns[1]: "antall"}, inplace=True)
    # "alle_dub" er alle linjer som er dublettert, hver for seg

    ant_rader_med_dub_verdier = len(alle_dub)
    ant_unike_dub_verdier = len(dub_frekvens)

    print(f"Distinkte dublett-verdier: {ant_unike_dub_verdier}")
    print(f"Fordelt på antall rader: {ant_rader_med_dub_verdier}")
    
    print("\nReturnert serie med unike dublettkombinasjoner: dub_frekvens")
    print("\nAlle rader i original-settet med dublettforekomster returneres ikke automatisk pga. diskplass, men kan lages slik utenfor funksjonen:")
    print("alle_dub = din_dataframe[din_dataframe.duplicated(subset=[din_variabelliste], keep=False)]")

    return dub_frekvens
