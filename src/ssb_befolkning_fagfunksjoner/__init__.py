"""Befolkning Fagfunksjoner."""

# Expose modules for convenient access
from . import date_utils
from . import klass_utils
from . import kommnr
from . import versions
from . import demographics
from . import generelle_sjekker

# Frequently used functions
from .versions import write_versioned_pandas
from .versions import get_latest_version_number
from .kommnr import update_kommnr
from .kommnr import validate_kommnr
from .kommnr import get_kommnr_changes
from .generelle_sjekker import dublettsjekk
from .generelle_sjekker import sml_rader


__all__ = [
    "date_utils",
    "klass_utils",
    "kommnr",
    "versions",
    "demographics",
    "generelle_sjekker",
    "write_versioned_pandas",
    "get_latest_version_number",
    "update_kommnr",
    "validate_kommnr",
    "get_kommnr_changes",
    "dublettsjekk",
    "sml_rader",
]
