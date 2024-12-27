"""This module contains functionality around dates for statistics production in S320."""

from .core import (
    get_period_dates,
    get_etterslep_dates,
    get_period_label,
)

from .date_tools import (
    get_next_period,
    get_last_period,
    get_last_day_of_next_month,
    get_last_day_of_month,
)

from input_function import get_user_inputs

__all__ = [
    "get_period_dates",
    "get_etterslep_dates",
    "get_period_label",
    "get_next_period",
    "get_last_period",
    "get_last_day_of_next_month",
    "get_last_day_of_month",
    "get_user_inputs",
]