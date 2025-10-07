"""Befolkning Fagfunksjoner."""

# Expose modules for convenient access
from . import date_utils
from . import klass_utils
from . import kommnr
from . import versions
from . import demographics

# Frequently used functions
from .versions import write_versioned_pandas
from .versions import get_latest_version_number
from .kommnr import update_kommnr
from .kommnr import validate_kommnr
from .kommnr import get_kommnr_changes

__all__ = [
    "date_utils",
    "klass_utils",
    "kommnr",
    "versions",
    "demographics",
    "write_versioned_pandas",
    "get_latest_version_number",
    "update_kommnr",
    "validate_kommnr",
    "get_kommnr_changes",
]
