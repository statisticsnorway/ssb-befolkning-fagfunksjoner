"""Subpackage for interacting with KLASS specifically used in population statistics."""

from .change_mapping import get_klass_change_mapping
from .komm_nr import get_komm_nr_changes
from .komm_nr import update_komm_nr
from .komm_nr import validate_komm_nr
from .level_mapping import aggregate_codes

__all__ = [
    "aggregate_codes",
    "get_klass_change_mapping",
    "get_komm_nr_changes",
    "update_komm_nr",
    "validate_komm_nr",
]
