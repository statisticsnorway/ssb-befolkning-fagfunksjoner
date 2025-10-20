import pandas as pd
import pytest
from pytest_mock import MockerFixture

from ssb_befolkning_fagfunksjoner.demographics.birth_rates import BirthRates

def test_beregn_middelfolkemengde():
    