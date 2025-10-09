"""Befolkning Fagfunksjoner."""

# Expose modules for convenient access
from . import date_utils
from . import demographics
from . import generelle_sjekker
from . import klass_utils
from . import kommnr
from . import versions
from .generelle_sjekker import dublettsjekk
from .generelle_sjekker import sml_rader
from .kommnr import get_kommnr_changes
from .kommnr import update_kommnr
from .kommnr import validate_kommnr
from .versions import get_latest_version_number

# Frequently used functions
from .versions import write_versioned_pandas

__all__ = [
    "date_utils",
    "demographics",
    "dublettsjekk",
    "generelle_sjekker",
    "get_kommnr_changes",
    "get_latest_version_number",
    "klass_utils",
    "kommnr",
    "sml_rader",
    "update_kommnr",
    "validate_kommnr",
    "versions",
    "write_versioned_pandas",
]
