"""Befolkning Fagfunksjoner."""

from ssb_befolkning_fagfunksjoner.date_utils import EventParams
from ssb_befolkning_fagfunksjoner.date_utils import get_last_day_of_month
from ssb_befolkning_fagfunksjoner.date_utils import get_last_day_of_next_month
from ssb_befolkning_fagfunksjoner.klass_utils import aggregate_codes
from ssb_befolkning_fagfunksjoner.klass_utils import get_klass_change_mapping
from ssb_befolkning_fagfunksjoner.klass_utils import get_kommnr_changes
from ssb_befolkning_fagfunksjoner.klass_utils import update_kommnr
from ssb_befolkning_fagfunksjoner.klass_utils import validate_kommnr

__all__ = [
    "EventParams",
    "aggregate_codes",
    "get_klass_change_mapping",
    "get_kommnr_changes",
    "get_last_day_of_month",
    "get_last_day_of_next_month",
    "update_kommnr",
    "validate_kommnr",
]
