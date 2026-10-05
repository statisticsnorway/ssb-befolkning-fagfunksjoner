"""Test cases for the parameters.prompts2 module."""

import argparse
from dataclasses import FrozenInstanceError
from datetime import date

import pytest

from ssb_befolkning_fagfunksjoner.parameters import prompts
from ssb_befolkning_fagfunksjoner.parameters.prompts import CancelledError
from ssb_befolkning_fagfunksjoner.parameters.prompts import NoInputError
from ssb_befolkning_fagfunksjoner.parameters.prompts import Parameter
from ssb_befolkning_fagfunksjoner.parameters.prompts import ParameterError
from ssb_befolkning_fagfunksjoner.parameters.prompts import add_arguments
from ssb_befolkning_fagfunksjoner.parameters.prompts import prompt
from ssb_befolkning_fagfunksjoner.parameters.validators import validate_bool
from ssb_befolkning_fagfunksjoner.parameters.validators import validate_reference_date

DATES = Parameter(
    "reference_dates",
    msg="Reference dates (YYYY-MM-DD, separated by spaces): ",
    validate_func=validate_reference_date,
    kind="list",
)
LETTERSLEP = Parameter("etterslep", msg="Include etterslep? (y/n)", kind="flag")
DRY_RUN = Parameter(
    "dry_run",
    validate_func=validate_bool,
    default=False,
    kind="flag",
    help="Do not write anything.",
)
PARAMS = [DATES, LETTERSLEP, DRY_RUN]

ALL_FROM_FLAGS = {
    "reference_dates": [date(2024, 1, 1), date(2024, 2, 1)],
    "etterslep": True,
    "dry_run": False,
}


def _answer(monkeypatch: pytest.MonkeyPatch, *answers: str) -> list[str]:
    """Feed canned answers to input() and return the questions that were shown."""
    shown: list[str] = []
    remaining = iter(answers)

    def fake_input(question: str = "") -> str:
        shown.append(question)
        return next(remaining)

    monkeypatch.setattr("builtins.input", fake_input)
    return shown


def _never_asked(monkeypatch: pytest.MonkeyPatch) -> None:
    """Fail loudly if anything asks a question that was not expected."""

    def unexpected(question: str = "") -> str:
        raise AssertionError(f"should not have asked: {question}")

    monkeypatch.setattr("builtins.input", unexpected)


def _parser() -> argparse.ArgumentParser:
    """Return a parser standing in for the caller's own."""
    return argparse.ArgumentParser(prog="script")


def _parse(parameters, argv) -> dict[str, object]:
    """Do what a script does: register parameters, parse, fill in the gaps."""
    return prompt(
        parameters, vars(add_arguments(_parser(), parameters).parse_args(argv))
    )


# ---------------- Parameter ----------------


def test_validate_func_defaults_to_str():
    p = Parameter("table")
    assert p.validate_func is str
    assert p.validate_func("2024-01-01") == "2024-01-01"


def test_a_flag_is_always_boolean(monkeypatch):
    # A flag from the command line, or from validate_bool when asked, is a bool.
    assert _parse([LETTERSLEP], ["--etterslep"]) == {"etterslep": True}
    _answer(monkeypatch, "y")
    assert prompt([LETTERSLEP], {}) == {"etterslep": True}
    _answer(monkeypatch, "no")
    assert prompt([LETTERSLEP], {}) == {"etterslep": False}


def test_the_validator_of_a_flag_is_a_yes_no_check():
    assert LETTERSLEP.validator is validate_bool
    assert DATES.validator is validate_reference_date
    assert Parameter("table").validator is str


@pytest.mark.parametrize(
    "name,flag",
    [("dry_run", "--dry-run"), ("reference_dates", "--reference-dates"), ("a", "--a")],
)
def test_underscores_in_names_become_dashes(name, flag):
    assert Parameter(name).flag == flag


def test_has_default_separates_false_from_unset():
    assert not Parameter("x").has_default
    assert Parameter("x", default=False).has_default
    assert Parameter("x", default=None).has_default


@pytest.mark.parametrize(
    "p,expected",
    [
        (Parameter("reference_dates"), "reference dates [q to cancel]"),
        (Parameter("x", msg="Include x? (y/n): "), "Include x? (y/n) [q to cancel]"),
        (Parameter("x", msg="Include x?"), "Include x? [q to cancel]"),
    ],
)
def test_user_input_label_trims_and_says_how_to_cancel(p, expected):
    assert p.user_input_label() == expected


def test_parameter_is_frozen():
    # A shared configuration should not be retunable by accident.
    field = "name"
    with pytest.raises(FrozenInstanceError):
        setattr(Parameter("x"), field, "y")


def test_parameter_is_hashable():
    assert len({Parameter("x"), Parameter("x")}) == 1


# ---------------- add_arguments ----------------


def test_add_arguments_registers_values_lists_and_flags():
    ns = add_arguments(_parser(), PARAMS).parse_args(
        ["--reference-dates", "2024-01-01", "2024-02-01", "--etterslep"]
    )
    assert ns.reference_dates == [date(2024, 1, 1), date(2024, 2, 1)]
    assert ns.etterslep is True
    assert ns.dry_run is None


def test_a_list_stops_at_the_next_flag():
    ns = add_arguments(_parser(), PARAMS).parse_args(
        ["--reference-dates", "2024-01-01", "--etterslep"]
    )
    assert ns.reference_dates == [date(2024, 1, 1)]


def test_a_value_is_converted_by_its_validator():
    assert _parse([DATES], ["--reference-dates", "20240101"]) == {
        "reference_dates": [date(2024, 1, 1)]
    }


def test_a_value_or_flag_that_was_not_supplied_is_none():
    # None is how prompt recognises that it still needs asking for, and it is
    # what keeps an absent flag distinct from one that was explicitly turned off.
    ns = add_arguments(_parser(), PARAMS).parse_args([])
    assert (ns.reference_dates, ns.etterslep, ns.dry_run) == (None, None, None)


@pytest.mark.parametrize(
    "argv,expected", [(["--etterslep"], True), (["--no-etterslep"], False)]
)
def test_a_flag_reads_both_ways_from_the_command_line(argv, expected):
    ns = add_arguments(_parser(), PARAMS).parse_args(argv)
    assert ns.etterslep is expected


@pytest.mark.parametrize(
    "argv,expected",
    [
        (["--etterslep", "--no-etterslep"], False),
        (["--no-etterslep", "--etterslep"], True),
    ],
)
def test_giving_both_spellings_of_a_flag_takes_the_last(argv, expected):
    # argparse gives one action two option strings, so it does not complain.
    # Pinning it so a future change to a mutually exclusive group is noticed.
    ns = add_arguments(_parser(), PARAMS).parse_args(argv)
    assert ns.etterslep is expected


def test_a_flag_defaulting_to_true_can_still_be_turned_off():
    on_by_default = Parameter("etterslep", kind="flag", default=True)
    parser = add_arguments(_parser(), [on_by_default])
    assert prompt([on_by_default], vars(parser.parse_args([]))) == {"etterslep": True}
    assert prompt([on_by_default], vars(parser.parse_args(["--no-etterslep"]))) == {
        "etterslep": False
    }


def test_the_validators_own_message_reaches_the_user(capsys):
    # Without the adapter, argparse reports "invalid <name> value" and the
    # explanation of what a good date looks like is lost.
    parser = add_arguments(_parser(), PARAMS)
    with pytest.raises(SystemExit) as excinfo:
        parser.parse_args(["--reference-dates", "nope"])
    assert excinfo.value.code == 2
    assert "Invalid reference-date 'nope'" in capsys.readouterr().err


def test_add_arguments_keeps_the_callers_own_arguments():
    parser = _parser()
    parser.add_argument("path")
    add_arguments(parser, PARAMS)
    ns = parser.parse_args(["somefile", "--etterslep"])
    assert ns.path == "somefile"


def test_add_arguments_shows_the_help_text():
    printed = add_arguments(_parser(), PARAMS).format_help()
    assert "Do not write anything." in printed


def test_add_arguments_returns_the_parser_it_was_given():
    parser = _parser()
    assert add_arguments(parser, []) is parser


# ---------------- prompt ----------------


def test_prompt_asks_only_for_what_is_missing(monkeypatch):
    # dry_run has a default and etterslep was typed, so only the dates are asked.
    shown = _answer(monkeypatch, "2024-01-01")
    values = prompt(PARAMS, {"etterslep": True})
    assert values == {
        "reference_dates": [date(2024, 1, 1)],
        "etterslep": True,
        "dry_run": False,
    }
    assert len(shown) == 1


def test_prompt_asks_with_the_parameters_own_question(monkeypatch):
    shown = _answer(monkeypatch, "2024-01-01", "y")
    prompt([DATES, LETTERSLEP], {})
    assert shown == [
        "Reference dates (YYYY-MM-DD, separated by spaces) [q to cancel]",
        "Include etterslep? (y/n) [q to cancel]",
    ]


def test_prompt_reads_everything_from_a_parser():
    assert (
        _parse(
            PARAMS,
            ["--reference-dates", "2024-01-01", "2024-02-01", "--etterslep"],
        )
        == ALL_FROM_FLAGS
    )


def test_prompt_prefers_a_default_over_asking(monkeypatch):
    _never_asked(monkeypatch)
    assert prompt([DRY_RUN], {}) == {"dry_run": False}


def test_prompt_trusts_a_value_of_false(monkeypatch):
    # Off is not the same as unknown.
    _never_asked(monkeypatch)
    assert prompt([Parameter("x", default=True)], {"x": False}) == {"x": False}


def test_a_flag_typed_on_the_command_line_is_not_asked_about(monkeypatch):
    _never_asked(monkeypatch)
    assert prompt([LETTERSLEP], {"etterslep": True}) == {"etterslep": True}


def test_a_flag_turned_off_on_the_command_line_is_not_asked_about(monkeypatch):
    _never_asked(monkeypatch)
    assert prompt([LETTERSLEP], {"etterslep": False}) == {"etterslep": False}


@pytest.mark.parametrize("known", [{}, {"etterslep": None}])
def test_a_flag_nobody_typed_is_asked_about(monkeypatch, known):
    shown = _answer(monkeypatch, "yes")
    assert prompt([LETTERSLEP], known) == {"etterslep": True}
    assert shown == ["Include etterslep? (y/n) [q to cancel]"]


def test_a_flag_nobody_typed_falls_back_to_its_default(monkeypatch):
    _never_asked(monkeypatch)
    assert prompt([DRY_RUN], {"dry_run": None}) == {"dry_run": False}


def test_prompt_splits_a_list_answer_on_whitespace(monkeypatch):
    _answer(monkeypatch, "2024-01-01   2024-02-01")
    assert prompt([DATES], {}) == {
        "reference_dates": [date(2024, 1, 1), date(2024, 2, 1)]
    }


def test_prompt_reports_a_bad_answer_and_asks_again(monkeypatch, capsys):
    shown = _answer(monkeypatch, "maybe", "n")
    assert prompt([Parameter("x", validate_func=validate_bool)], {}) == {"x": False}
    assert "true/false" in capsys.readouterr().out
    assert len(shown) == 2


def test_prompt_reports_a_bad_item_in_a_list_answer(monkeypatch, capsys):
    _answer(monkeypatch, "2024-01-01 nope", "2024-01-01")
    prompt([DATES], {})
    assert "Invalid reference-date 'nope'" in capsys.readouterr().out


def test_prompt_asks_again_after_an_empty_list_answer(monkeypatch, capsys):
    shown = _answer(monkeypatch, "   ", "2024-01-01")
    assert prompt([DATES], {}) == {"reference_dates": [date(2024, 1, 1)]}
    assert "Enter at least one value." in capsys.readouterr().out
    assert len(shown) == 2


@pytest.mark.parametrize("answer", ["q", "Q", "quit", "QUIT", "exit", "Exit"])
def test_prompt_stops_when_the_user_cancels(monkeypatch, answer):
    _answer(monkeypatch, answer)
    with pytest.raises(CancelledError):
        prompt([LETTERSLEP], {})


def test_cancelling_is_also_a_keyboard_interrupt(monkeypatch):
    # So that an existing KeyboardInterrupt handler still stops the run.
    _answer(monkeypatch, "q")
    with pytest.raises(KeyboardInterrupt):
        prompt([LETTERSLEP], {})


def test_prompt_reports_when_input_runs_out(monkeypatch):
    def at_end_of_file(prompt: str = "") -> str:
        raise EOFError

    monkeypatch.setattr("builtins.input", at_end_of_file)
    with pytest.raises(NoInputError, match="there is none"):
        prompt([LETTERSLEP], {})


def test_prompt_treats_missing_known_as_empty():
    assert prompt([Parameter("x", default="d")], None) == {"x": "d"}


def test_prompt_returns_one_entry_per_parameter(monkeypatch):
    _answer(monkeypatch, "2024-01-01", "y", "n")
    assert set(prompt(PARAMS, {})) == {
        "reference_dates",
        "etterslep",
        "dry_run",
    }


def test_prompt_never_asks_when_everything_is_known(monkeypatch):
    _never_asked(monkeypatch)
    assert prompt(PARAMS, dict(ALL_FROM_FLAGS)) == ALL_FROM_FLAGS


# ---------------- the same script, both ways ----------------


def test_the_same_parameters_serve_the_terminal_and_the_question(monkeypatch):
    from_flags = _parse(
        PARAMS, ["--reference-dates", "2024-01-01", "2024-02-01", "--etterslep"]
    )
    shown = _answer(monkeypatch, "2024-01-01 2024-02-01", "y", "n")
    from_questions = prompt(PARAMS, {})
    assert from_flags == from_questions == ALL_FROM_FLAGS
    # Only the dates are asked interactively; dry_run has a default.
    assert len(shown) == 2


# ---------------- the errors themselves ----------------


@pytest.mark.parametrize("error", [CancelledError, NoInputError])
def test_every_error_can_be_caught_as_a_parameter_error(error):
    assert issubclass(error, ParameterError)


def test_only_cancelling_is_a_keyboard_interrupt():
    assert issubclass(CancelledError, KeyboardInterrupt)
    assert not issubclass(NoInputError, KeyboardInterrupt)


def test_everything_exported_actually_exists():
    assert all(hasattr(prompts, name) for name in prompts.__all__)
