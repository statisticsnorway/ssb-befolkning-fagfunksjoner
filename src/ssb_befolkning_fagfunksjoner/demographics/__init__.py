"""Demographic computation used in population statistics."""

from .birth_rates import foedselsrate
from .birth_rates import samlet_fruktbarhet
from .order_country_codes import order_country_codes

__all__ = ["foedselsrate", "order_country_codes", "samlet_fruktbarhet"]
