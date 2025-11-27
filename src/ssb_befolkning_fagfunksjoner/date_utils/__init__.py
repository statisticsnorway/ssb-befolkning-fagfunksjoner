"""Date utility subpackage for date logic in population statistics."""

from .event_params import EventParams
from .dates import (
    get_last_day_of_month,
    get_last_day_of_next_month
)


__all__ = [
    "EventParams",
    "get_last_day_of_month",
    "get_last_day_of_next_month",
]
