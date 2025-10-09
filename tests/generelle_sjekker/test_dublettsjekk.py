import pandas as pd

# 13 rows with duplicates:
# - "person_2" appears twice
# - "person_7" appears three times
# - score "25" appears twice
test_data = pd.DataFrame(
    {
        "name": [f"person_{i}" for i in range(1, 11)] + ["person_2"] + ["person_7"] * 2,
        "score": [88, 76, 64, 91, 70, 62, 55, 80, 67, 73, 25, 25, 84],
    }
)


def test_dublettsjekk_series() -> None:
    """Kjører på serie:
    dublettsjekk(inndata=testsett1["Name"])
    """
    pass


def test_dublettsjekk_dataframe() -> None:
    """Kjører på enkeltkolonne fra dataframe:
    dublettsjekk(inndata=testsett1, variabler=["Name"])

    Kjører på flere kolonner fra dataframe:
    dublettsjekk(inndata=testsett1, variabler=["Name", "Score"])
    """
    pass
