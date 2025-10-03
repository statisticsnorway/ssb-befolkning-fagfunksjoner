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


def test_dublettsjekk_series():
    """
    Kjører på serie:
    dublettsjekk(inndata=testsett1["Name"])
    """
    pass


def test_dublettsjekk_dataframe():
    """
    Kjører på enkeltkolonne fra dataframe:
    dublettsjekk(inndata=testsett1, variabler=["Name"])

    Kjører på flere kolonner fra dataframe:
    dublettsjekk(inndata=testsett1, variabler=["Name", "Score"])
    """
    pass