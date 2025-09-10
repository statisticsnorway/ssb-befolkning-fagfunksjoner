import pandas as pd
import numpy as np

# Create a DataFrame with 10 rows and 2 columns
data = {
    "Name": [f"Person_{i}" for i in range(1, 14)],
    "Score": np.random.randint(50, 100, size=13)
}

testsett1 = pd.DataFrame(data)
testsett1.loc[0, "Name"] = "Person_2"
testsett1.loc[4, "Name"] = "Person_7"
testsett1.loc[5, "Name"] = "Person_7"
testsett1.loc[4, "Score"] = 25
testsett1.loc[5, "Score"] = 25
print(testsett1)




def dublettsjekk(
    inndata: pd.DataFrame | pd.Series,    
    variabler=None):

        """
    Printer antall unike verdier som forekommer to eller flere ganger.
    Printer hvor mange rader disse verdiene fordeler seg på.
    Returnerer dub_frekvens med hvilke verdier det gjelder, og frekvens for hver verdi.

    (Printer syntaks for å hente alle rader, med alle kolonner, som er representert )

    Input kan være en serie:
    dublettsjekk(inndata=testsett1, variabler=["Name"])
    dublettsjekk(inndata=testsett1, variabler=["Name", "Score"])
    dublettsjekk(inndata=testsett1["Name"])


    - Teller og printer antall rader i parameter1
    - Teller og printer antall rader i parameter2
    - Printer differansen



    Eksempler med testdata:
    import pandas as pd
    import numpy as np

    # Create a DataFrame with 10 rows and 2 columns
    data = {
        "Name": [f"Person_{i}" for i in range(1, 14)],
        "Score": np.random.randint(50, 100, size=13)
    }

    testsett1 = pd.DataFrame(data)
    testsett1.loc[0, "Name"] = "Person_2"
    testsett1.loc[4, "Name"] = "Person_7"
    testsett1.loc[5, "Name"] = "Person_7"
    testsett1.loc[4, "Score"] = 25
    testsett1.loc[5, "Score"] = 25
    print(testsett1)

    Kjører på enkeltkolonne fra dataframe:
    dublettsjekk(inndata=testsett1, variabler=["Name"])

    Kjører på flere kolonner fra dataframe:
    dublettsjekk(inndata=testsett1, variabler=["Name", "Score"])

    Kjører på serie:
    dublettsjekk(inndata=testsett1["Name"])
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
    

dublettsjekk(inndata=testsett1, variabler=["Name"])
dublettsjekk(inndata=testsett1, variabler=["Name", "Score"])
dublettsjekk(inndata=testsett1["Name"])

dub_frekvens.info()
dub_frekvens

    

dub_frekvens