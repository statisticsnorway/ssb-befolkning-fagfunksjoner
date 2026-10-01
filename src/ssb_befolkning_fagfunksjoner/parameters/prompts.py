import argparse
from dataclasses import dataclass
from typing import Any
from typing import Callable

from ssb_befolkning_fagfunksjoner.parameters.validators import validate_bool

CANCEL = {"q", "quit", "exit"}


@dataclass
class Parameter:
    name: str
    msg: str
    validate_func: Callable[[str], Any]
    accept_multiple_args: bool = False


def _is_interactive() -> bool:
    try:
        from IPython.core.getipython import get_ipython
    except ImportError:
        return False
    return get_ipython() is not None


def _prompt_parameter(
    msg: str,
    validate_func: Callable[[str], Any],
    accept_multiple_args: bool = False,
    value: Any | None = None,
) -> Any:
    """Return 'value' if given, otherwise prompt until valid or cancelled.

    Type q / quit / exit to cancel (raises KeyboardInterrupt)
    """
    if value is not None:
        return value
    while True:
        user_input = input(f"{msg}('q' to cancel) ").strip()
        if user_input.casefold() in CANCEL:
            raise KeyboardInterrupt("Cancelled by user.")
        try:
            if not accept_multiple_args:
                return validate_func(user_input)
            items = user_input.split()
            if not items:
                raise ValueError("Enter at least one value.")
            return [validate_func(item) for item in items]
        except ValueError as e:
            print(e)


def _argparse_type(func: Callable[[str], Any]) -> Callable[[str], Any]:
    """Make argparse show the validator's own error message."""
 
    def wrapper(s: str) -> Any:
        try:
            return func(s)
        except ValueError as e:
            raise argparse.ArgumentTypeError(str(e)) from None
 
    return wrapper


def _parse_cli(parameters: list[Parameter]) -> dict[str, Any]:
    """Parse command line flags into {name: value}; None for flags not given."""
    parser = argparse.ArgumentParser()
    for p in parameters:
        flag = "--" + p.name.replace("_", "-")
        if p.validate_func is validate_bool:
            parser.add_argument(
                flag,
                dest=p.name,
                action=argparse.BooleanOptionalAction
            )
        else:
            parser.add_argument(
                flag,
                dest=p.name,
                type=_argparse_type(p.validate_func),
                nargs="+" if p.accept_multiple_args else None
            )
    return vars(parser.parse_args())


def get_run_parameters(parameters: list[Parameter]) -> dict[str, Any]:
    """Return {name: value} for each parameter.

    Uses command line flags when run from a terminal and prompts anything
    missing. Always prompts when run interactively.
    """
    cli = {} if _is_interactive() else _parse_cli(parameters)
    return {
        p.name: _prompt_parameter(p.msg, p.validate_func, p.accept_multiple_args, cli.get(p.name))
        for p in parameters
    }
