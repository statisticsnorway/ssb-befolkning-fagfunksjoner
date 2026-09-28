"""Input/Output functions used in production of population statistics."""

from .io import read_csv_case_indep_pd
from .io import read_csv_case_indep_pl

__all__ = [
    "read_csv_case_indep_pd",
    "read_csv_case_indep_pl",
]
