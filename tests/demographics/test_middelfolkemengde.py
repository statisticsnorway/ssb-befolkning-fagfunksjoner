import pandas as pd
import pytest
from pytest_mock import MockerFixture

from ssb_befolkning_fagfunksjoner.demographics.birth_rates import BirthRates


@pytest.fixture
def n_df_start():
    return pd.DataFrame(
        {"aldersgruppe": [25, 30], "kjoenn": ["2", "2"], "landsdel": ["A", "B"]}
    )


@pytest.fixture
def n_df_slutt():
    return pd.DataFrame(
        {"alder": [31, 30], "kjoenn": ["2", "2"], "landsdel": ["B", "B"]}
    )
