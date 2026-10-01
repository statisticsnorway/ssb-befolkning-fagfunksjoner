"""Set of validator functions: str -> parsed value

Raises ValueError if invalid
"""
from typing import Callable
import datetime

TRUE = {"true", "yes", "y", "1"}
FALSE = {"false", "no", "n", "0"}


def validate_reference_date(s: str) -> datetime.date:
    """Validate and return a date from a date string.

    Args:
        s: The date string in format YYYY-MM-DD or YYYYMMDD.
    
    Returns:
        date: The validated date object.

    Raises:
        ValueError: If the string is not a valid date.
    """
    if len(s) not in (8, 10):
        raise ValueError(f"Invalid reference-date '{s}'. Expected YYYY-MM-DD or YYYYMMDD.")
    try:
        return datetime.date.fromisoformat(s)
    except ValueError:
        try:
            return datetime.datetime.strptime(s, "%Y%m%d").date()
        except ValueError as e:
            raise ValueError(f"Invalid reference-date '{s}'. Expected YYYY-MM-DD or YYYYMMDD.") from e


def validate_bool(s: str) -> bool:
    normalised = s.strip().casefold()
    if normalised in TRUE:
        return True
    if normalised in FALSE:
        return False
    raise ValueError("Enter true/false, yes/no, y/n, or 1/0.")


def int_in_range(low: int = 0, high: int | None = None) -> Callable[[str], int]:

    def validate_int(s: str) -> int:
        try:
            n = int(s.strip())
        except ValueError:
            raise ValueError(f"'{s}' is not a valid integer.") from None
        if n < low or (high is not None and n > high):
            bounds = f"between {low} and {high}" if high is not None else f"of at least {low}"
            raise ValueError(
                f"Enter a value {bounds}."
            )
        return n
    
    return validate_int


def choice(options: tuple[str, ...]) -> Callable[[str], str]:
    """Return a validator accepting an option or an unambiguous prefix of one."""
 
    def validate(s: str) -> str:
        text = s.strip().casefold()
        if text in options:
            return text
        matches = [o for o in options if text and o.startswith(text)]
        if len(matches) == 1:
            return matches[0]
        raise ValueError(f"Choose one of: {'/'.join(options)}.")
 
    return validate
