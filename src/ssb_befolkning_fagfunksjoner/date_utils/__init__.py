"""Date utility subpackage for date logic in population statistics."""

from .dates import get_last_day_of_month
from .dates import get_last_day_of_next_month
from .event_params import EventParams

__all__ = [
    "EventParams",
    "get_last_day_of_month",
    "get_last_day_of_next_month",
]
