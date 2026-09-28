from pathlib import Path

import polars as pl
import pytest

from ssb_befolkning_fagfunksjoner.io.io import read_csv_case_indep_pd
from ssb_befolkning_fagfunksjoner.io.io import read_csv_case_indep_pl


@pytest.fixture()
def temp_csv_file(tmp_path: Path) -> Path:
    csv_file = tmp_path / "test_data.csv"
    # Create a CSV with semi-colon separator and mixed-case headers
    content = "FNR;FoedselsDato;KOMMNR;value\n12345678901;2024-01-01;0301;10\n98765432109;1990-12-31;4601;20\n"
    csv_file.write_text(content, encoding="utf-8")
    return csv_file


def test_read_csv_case_indep_pd_select_cols(temp_csv_file: Path) -> None:
    df = read_csv_case_indep_pd(temp_csv_file, cols=["fnr", "foedselsdato"], sep=";", dtype={"FNR": str})
    
    assert list(df.columns) == ["fnr", "foedselsdato"]
    assert len(df) == 2
    assert df.loc[0, "fnr"] == "12345678901"
    assert df.loc[1, "foedselsdato"] == "1990-12-31"


def test_read_csv_case_indep_pd_all_cols(temp_csv_file: Path) -> None:
    df = read_csv_case_indep_pd(temp_csv_file, cols=None, sep=";")
    
    assert list(df.columns) == ["fnr", "foedselsdato", "kommnr", "value"]
    assert len(df) == 2


def test_read_csv_case_indep_pd_missing_col(temp_csv_file: Path) -> None:
    with pytest.raises(ValueError, match="Cannot find columns"):
        read_csv_case_indep_pd(temp_csv_file, cols=["fnr", "non_existent_col"], sep=";")


def test_read_csv_case_indep_pl_select_cols(temp_csv_file: Path) -> None:
    df = read_csv_case_indep_pl(temp_csv_file, cols=["fnr", "foedselsdato"], separator=";", dtypes={"FNR": pl.String})
    
    assert list(df.columns) == ["fnr", "foedselsdato"]
    assert len(df) == 2
    assert df.item(0, "fnr") == "12345678901"
    assert df.item(1, "foedselsdato") == "1990-12-31"


def test_read_csv_case_indep_pl_all_cols(temp_csv_file: Path) -> None:
    df = read_csv_case_indep_pl(temp_csv_file, cols=None, separator=";")
    
    assert list(df.columns) == ["fnr", "foedselsdato", "kommnr", "value"]
    assert len(df) == 2


def test_read_csv_case_indep_pl_missing_col(temp_csv_file: Path) -> None:
    with pytest.raises(ValueError, match="Cannot find columns"):
        read_csv_case_indep_pl(temp_csv_file, cols=["fnr", "non_existent_col"], separator=";")
