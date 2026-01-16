import pandas as pd


def sml_rader(dataframe1: pd.DataFrame, dataframe2: pd.DataFrame) -> None:
    """Sjekker om to datasett har likt antall rader. Til å sjekke at f.eks. joins ikke har skapt flere rader ved et uhell.

    - Teller og printer antall rader i parameter1
    - Teller og printer antall rader i parameter2
    - Printer differansen

    Eksempel på bruk:

    import pandas as pd
    import numpy as np

    # Create a DataFrame with 10 rows and 2 columns
    data = {
        "Name": [f"Person_{i}" for i in range(1, 11)],
        "Score": np.random.randint(50, 100, size=10)
    }

    tellesett1 = pd.DataFrame(data)

    print(tellesett1)


    data = {
        "Name": [f"Person_{i}" for i in range(1, 14)],
        "Score": np.random.randint(50, 100, size=13)
    }

    tellesett2 = pd.DataFrame(data)

    print(tellesett2)



    sml_rader("tellesett1", "tellesett2")


    """
    row_count1 = len(dataframe1)
    row_count2 = len(dataframe2)
    smldiff = row_count2 - row_count1

    print(f"Rader i {dataframe1}: {row_count1}")
    print(f"Rader i {dataframe2}: {row_count2}")
    print(f"Endring: {smldiff}")
