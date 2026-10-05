"""Functions to configure run parameters used in population statistics."""

from .prompts import Parameter
from .prompts import add_arguments
from .prompts import prompt
from .prompts import ParameterError
from .validators import validate_bool
from .validators import validate_reference_date
from .validators import int_in_range
from .validators import choice

__all__ = [
    "Parameter",
    "ParameterError",
    "add_arguments",
    "prompt",
    "validate_bool",
    "validate_reference_date",
    "int_in_range",
    "choice",
]
