"""Collecting the values a run needs, from flags or by asking.

A script that owns its command line registers its parameters on an argparse
parser and hands the parsed arguments to :func:`prompt`. Anything not supplied
is asked for, so the same script runs with flags from the terminal, or with no
flags at all and a question for each value.
"""

import argparse
from collections.abc import Callable
from collections.abc import Mapping
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any
from typing import Literal

from ssb_befolkning_fagfunksjoner.parameters.validators import validate_bool

__all__ = [
    "CANCEL",
    "CancelledError",
    "NoInputError",
    "Parameter",
    "ParameterError",
    "add_arguments",
    "prompt",
]

CANCEL = frozenset({"q", "quit", "exit"})

NO_DEFAULT = object()

ParameterKind = Literal["value", "flag", "list"]


class ParameterError(Exception):
    """Anything this module raises, so a caller can catch one thing."""


class CancelledError(ParameterError, KeyboardInterrupt):
    """The user cancelled. KeyboardInterrupt, so existing handlers still stop."""


class NoInputError(ParameterError):
    """A value was needed, but there was nobody there to ask."""


@dataclass(frozen=True)
class Parameter:
    """One value the run needs.

    Args:
        name: Becomes the key in the returned dict.
        msg: The question to ask. Defaults to the name.
        validate_func: Turns a string into the required value.
            Defaults to :func:`str`, which accepts anything.
            Not used for ``kind="flag"``, which is always boolean.
        kind: Kind of parameter.
            ``"value"`` takes one argument,
            ``"list"`` takes one or more,
            ``"flag"`` is a switch read as ``--flag`` or ``--no-flag``.
        default: Used instead of asking when nothing was supplied.
        help: Description shown by ``--help``.
    """

    name: str
    msg: str = ""
    validate_func: Callable[[str], Any] = str
    kind: ParameterKind = "value"
    default: Any = NO_DEFAULT
    help: str = ""
        

    @property
    def has_default(self) -> bool:
        """Whether a value is available without asking anyone."""
        return self.default is not NO_DEFAULT

    @property
    def validator(self) -> Callable[[str], Any]:
        """The callable that turns typed text into this parameter's value.

        A flag is a yes/no question, so it always answers with a boolean.
        """
        return validate_bool if self.kind == "flag" else self.validate_func

    @property
    def flag(self) -> str:
        """The command line flag this parameter is read from."""
        return f"--{self.name.replace('_', '-')}"

    def user_input_label(self) -> str:
        """The question to put in front of the user, taken from ``msg`` as given."""
        question = (
            (self.msg or self.name.replace("_", " ")).rstrip().rstrip(":").rstrip()
        )
        return f"{question} [q to cancel]"


def add_arguments(
    parser: argparse.ArgumentParser, parameters: Sequence[Parameter]
) -> argparse.ArgumentParser:
    """Register parameters on a parser the caller owns.

    A value that was not supplied is left as None, which is how :func:`prompt`
    recognises that it still needs asking for.

    Args:
        parser: The parser to add to.
        parameters: The parameters the parser should understand.

    Returns:
        The same parser, so calls can be chained.
    """
    _check_parameters(parameters)
    
    for p in parameters:
        if p.kind == "flag":
            # BooleanOptionalAction gives --flag and --no-flag, and leaves an absent flag as None
            parser.add_argument(
                p.flag,
                dest=p.name,
                action=argparse.BooleanOptionalAction,
                default=None,
                help=p.help or None,
            )
        else:
            parser.add_argument(
                p.flag,
                dest=p.name,
                type=_argument_type(p.validate_func),
                nargs="+" if p.kind == "list" else None,
                default=None,
                metavar="VALUE",
                help=p.help or None,
            )
    return parser


def _argument_type(validate: Callable[[str], Any]) -> Callable[[str], Any]:
    """Adapt a validator to what argparse expects from a ``type=`` callable.

    argparse replaces the message of a bare ValueError with its own generic
    "invalid <name> value". Raising ArgumentTypeError instead is what lets the
    explanation the validator wrote reach the user.
    """

    def _validation_wrapper(text: str) -> Any:
        try:
            return validate(text)
        except ValueError as e:
            raise argparse.ArgumentTypeError(str(e)) from None

    return _validation_wrapper


def prompt(
    parameters: Sequence[Parameter],
    known: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Return every parameter's value, asking only for what is missing.

    Args:
        parameters: The parameters to fill in.
        known: Values already read from the command line, typically
            ``vars(parser.parse_args())``.

    Returns:
        A dict with one entry per parameter, in the order given.

    Raises:
        CancelledError: If the user cancels.
        NoInputError: If a value was needed but input was unavailable.
    """
    _check_parameters(parameters)
    
    known = known or {}
    values: dict[str, Any] = {}
    for p in parameters:
        # None is the only thing that counts as missing, for every kind: an
        # absent value, and an absent or unanswered flag alike.
        given = known.get(p.name)
        if given is not None:
            if p.kind == "flag" and not isinstance(given, bool):
                raise ParameterError(
                    f"Value for {p.name!r} must be boolean."
                )
            values[p.name] = given
        elif p.has_default:
            values[p.name] = p.default
        else:
            values[p.name] = _ask_for(p)
    return values


def _ask_for(p: Parameter) -> Any:
    """Keep asking until the answer validates, or the user gives up."""
    while True:
        try:
            user_input = input(p.user_input_label()).strip()
        except EOFError as e:
            raise NoInputError(
                "Input was needed but there is none. Supply the values as flags, "
                "or give every parameter a default."
            ) from e

        if user_input.casefold() in CANCEL:
            raise CancelledError(f"Cancelled at '{p.name}'.")
        try:
            if p.kind == "list":
                items = user_input.split()
                if not items:
                    raise ValueError("Enter at least one value.")
                return [p.validator(item) for item in items]
            return p.validator(user_input)
        except ValueError as e:
            print(e)


def _check_parameters(parameters: Sequence[Parameter]) -> None:
    """Reject invalid or ambiguous parameter definitions."""
    names = set()

    for p in parameters:
        if not p.name.strip():
            raise ParameterError("Parameter names must not be empty.")

        if p.kind not in {"value", "flag", "list"}:
            raise ParameterError(f"Unknown kind: {p.kind!r}.")

        if p.name in names:
            raise ParameterError(f"Duplicate parameter {p.name!r}.")

        if p.kind == "flag" and p.has_default and not isinstance(p.default, bool):
            raise ParameterError(f"Default for {p.name!r} must be boolean.")

        names.add(p.name)