"""Subpackage for demographic computations used in population statistics."""

from .birth_rates import foedselsrate
from .birth_rates import samlet_fruktbarhet
from .order_country_codes import sorter_landkoder

__all__ = ["foedselsrate", "samlet_fruktbarhet", "sorter_landkoder"]
