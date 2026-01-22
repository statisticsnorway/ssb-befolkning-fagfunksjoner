"""Subpackage for demographic computations used in population statistics."""

from .birth_rates import foedselsrate, samlet_fruktbarhet

__all__ = [
    "foedselsrate",
    "samlet_fruktbarhet",
]
