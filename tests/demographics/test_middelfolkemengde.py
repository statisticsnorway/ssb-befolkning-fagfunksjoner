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


def test_beregn_middelfolkemengde(
    mocker: MockerFixture,
    br_default: BirthRates,
) -> None:
    mock_gruppert = mocker.patch.object(br_default, "_tell_per_gruppe")
    mock_gruppert.side_effect = [n_df_start, n_df_slutt]
