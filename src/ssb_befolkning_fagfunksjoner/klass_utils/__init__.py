"""Subpackage for interacting with KLASS specifically used in population statistics."""

from .change_mapping import get_klass_change_mapping
from .level_mapping import aggregate_codes

__all__ = ["aggregate_codes", "get_klass_change_mapping"]
