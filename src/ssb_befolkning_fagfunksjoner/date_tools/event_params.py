import calendar
import sys
from datetime import date
from typing import Literal
from typing import Self

from dateutil.relativedelta import relativedelta

if sys.version_info >= (3, 13):
    from typing import TypeIs
else:
    from typing_extensions import TypeIs

type PeriodType = Literal["year", "halfyear", "quarter", "month", "week"]


class EventParams:
    """Class for handling event periods.

    Attributes:
        VALID_PERIOD_TYPES: Compatible period types.

    Validates and stores a statistical period (e.g. a quarter or a month), computes
    the calendar window, creates a Dapla-standardised period label, and exposes
    event parameters as SQL query parameters.

    Examples:
        >>> event_params = EventParams(year=2026, period_type="quarter", period_number=2)
        >>> event_params.period_label
        '2026-Q2'
        >>> event_params.window
        (datetime.date(2026, 4, 1), datetime.date(2026, 6, 30))
    """

    VALID_PERIOD_TYPES: tuple[PeriodType, ...] = (
        "year",
        "halfyear",
        "quarter",
        "month",
        "week",
    )

    def __init__(
        self,
        year: int | None = None,
        period_type: str | None = None,
        period_number: int | None = None,
        specify_wait_period: bool = False,
    ) -> None:
        """Initialises an EventParams instance.

        Any argument left as `None` triggers an interactive prompt. If
        `specify_wait_period` is `True`, the user is also prompted for
        period-lag attributes. Otherwise, period-lag defaults to 1 month and 0 days.

        Args:
            year: The calendar year of the period. Prompted if `None`.
            period_type: Granularity of the period. Must be one of
                `VALID_PERIOD_TYPES`. Prompted if `None` or invalid.
            period_number: Ordinal position within the year (e.g. `2` for
                February or Q2). Ignored for `"year"` periods; prompted if
                `None` for all other types.
            specify_wait_period: If `True`, interactively prompt the user for
                `wait_months` and `wait_days` instead of using the defaults.
        """
        year, period_type, period_number = self._prompt_missing_values(
            year, period_type, period_number
        )

        self.year: int = year
        self.period_type: PeriodType = period_type
        self.period_number: int | None = period_number
        self.specify_wait_period: bool = specify_wait_period

        # Lag parameters default to 1 month and 0 days if specify_wait_period is False
        if specify_wait_period:
            self.wait_months, self.wait_days = self._prompt_etterslep_values()
        else:
            self.wait_months, self.wait_days = 1, 0

    # --------------------------------------------------------------------
    # Prompting functions
    # --------------------------------------------------------------------
    @classmethod
    def _prompt_missing_values(
        cls: type[Self],
        year: int | None,
        period_type: str | None,
        period_number: int | None,
    ) -> tuple[int, PeriodType, int | None]:
        """Prompt user for missing input arguments.

        Validates `period_type` and only prompts for `period_number` when
        period is not `"year"`.

        Args:
            year: The calendar year, or `None` to trigger a prompt.
            period_type: The period granularity, or `None` / an invalid string
                to trigger a prompt.
            period_number: The ordinal period number, or `None` to trigger a
                prompt for non-year period types.

        Returns:
            A three-tuple of `(year, period_type, period_number)`.
        """
        if year is None:
            year = cls._prompt_year()

        if period_type is None or not cls._check_period_type(period_type):
            period_type = cls._prompt_period_type("Enter period type")

        # Only prompt period number when relevant
        if period_type == "year":
            period_number = None
        elif period_number is None:
            if period_type == "halfyear":
                period_number = cls._prompt_int_in_range(
                    "Enter halfyear number", (1, 2)
                )
            if period_type == "quarter":
                period_number = cls._prompt_int_in_range("Enter quarter number", (1, 4))
            if period_type == "month":
                period_number = cls._prompt_int_in_range("Enter month number", (1, 12))
            if period_type == "week":
                period_number = cls._prompt_int_in_range("Enter week number", (1, 53))

        return year, period_type, period_number

    @classmethod
    def _check_period_type(cls: type[Self], value: str) -> TypeIs[PeriodType]:
        """Checks whether a string is a valid period type.

        Args:
            value: The string to validate.

        Returns:
            `True` if `value` is one of `VALID_PERIOD_TYPES`, `False` otherwise.
        """
        return value in cls.VALID_PERIOD_TYPES

    @classmethod
    def _prompt_etterslep_values(cls: type[Self]) -> tuple[int, int]:
        """Prompts the user for wait period.

        Returns:
            A two-tuple of `(wait_months, wait_days)`.
        """
        wait_months = cls._prompt_int_in_range("Enter wait months")
        wait_days = cls._prompt_int_in_range("Enter wait days")

        return wait_months, wait_days

    @classmethod
    def _prompt_period_type(cls: type[Self], msg: str) -> PeriodType:
        """Prompts the user for period type with instant validity feedback.

        Accepts both full names (e.g. `"quarter"`) and their first-letter
        abbreviations (e.g. `"q"`). Loops until a valid choice is entered.

        Args:
            msg: The prompt message displayed to the user.

        Returns:
            A validated `PeriodType` string.
        """
        abbreviations: dict[str, PeriodType] = {
            c[0]: c for c in cls.VALID_PERIOD_TYPES
        }  # e.g. {"m": "month", "q": "quarter"}
        valid_choices_str = "/".join(cls.VALID_PERIOD_TYPES)

        while True:
            value = input(f"{msg} ({valid_choices_str}): ").strip().lower()

            if value in abbreviations:
                return abbreviations[value]

            if cls._check_period_type(value):
                return value

            print(
                f"'{value}' is not a valid option. Please choose one of: {valid_choices_str}."
            )

    @staticmethod
    def _prompt_int_in_range(
        msg: str, valid_range: tuple[int, int] | None = None
    ) -> int:
        """Prompt user for an integer, optionally constrained to a range.

        Loops until a valid choice is entered.

        Args:
            msg: The prompt message displayed to the user.
            valid_range: An inclusive bound.

        Returns:
            A validated integer.
        """
        if valid_range is not None:
            low, high = valid_range
            prompt_msg = f"{msg} ({low}-{high}): "
        else:
            prompt_msg = f"{msg}: "

        while True:
            value_str = input(prompt_msg).strip()

            # Basic integer check
            if not value_str.isdigit():
                print(f"'{value_str}' is not a valid integer. Please enter a number.")
                continue

            value_int = int(value_str)

            # Range check
            if valid_range is not None and not (low <= value_int <= high):
                print(f"Please enter a value between {low} and {high}.")
                continue

            return value_int

    @classmethod
    def _prompt_year(cls) -> int:
        """Prompts the user for calendar year between 1900 and current year.

        Returns:
            A validated 4-digit year.
        """
        current_year = date.today().year
        return cls._prompt_int_in_range("Enter year", (1900, current_year))

    # --------------------------------------------------------------------
    # Properties
    # --------------------------------------------------------------------
    @property
    def period_label(self) -> str:
        """Formats the period as a Dapla-standardised label string.

        Returns:
            A period label in the appropriate format for the period type:

            - `"year"`     → `"2024"`
            - `"halfyear"` → `"2024-H1"`
            - `"quarter"`  → `"2024-Q3"`
            - `"month"`    → `"2024-06"`
            - `"week"`     → `"2024-W09"`

        Raises:
            ValueError: If `period_type` is not a recognised value.
        """
        if self.period_type == "year":
            return f"{self.year}"

        if self.period_type == "halfyear":
            return f"{self.year}-H{self.period_number}"

        if self.period_type == "quarter":
            return f"{self.year}-Q{self.period_number}"

        if self.period_type == "month":
            return f"{self.year}-{str(self.period_number).zfill(2)}"

        if self.period_type == "week":
            return f"{self.year}-W{str(self.period_number).zfill(2)}"

        raise ValueError()

    @property
    def etterslep_label(self) -> str:
        """Formats the wait period as a compact label string.

        Returns:
            A string of the form `"{months}m{days}d"`, e.g. `"1m0d"`.
                Defaults to `"1m0d"` when `specify_wait_period` is `False`.
        """
        return f"{self.wait_months}m{self.wait_days}d"

    @property
    def window(self) -> tuple[date, date]:
        """Computes the calendar window for the period.

        The end date is the *last* day of the period (inclusive bound), e.g.
        `date(2026, 3, 31)` for Q1 2026.

        Returns:
            A `(start_date, end_date)` tuple.

        Raises:
            ValueError: If `year` is None, or if `period_number` is
                `None` in a non-year period.
        """
        y = self.year
        if y is None:
            raise ValueError("'year' is not set. Cannot derive window.")

        pt = self.period_type
        if pt == "year":
            start = date(y, 1, 1)
            end = date(y, 12, 31)
            return start, end

        pn = self.period_number
        if pn is None:
            raise ValueError(
                "'period_number' is not set. Cannot derive window for non-year periods."
            )

        if pt == "halfyear":
            start_month = 1 if pn == 1 else 7
            start = date(y, start_month, 1)
            end = start + relativedelta(months=6) - relativedelta(days=1)
            return start, end

        if pt == "quarter":
            start_month = (pn - 1) * 3 + 1
            start = date(y, start_month, 1)
            end = start + relativedelta(months=3) - relativedelta(days=1)
            return start, end

        if pt == "month":
            start = date(y, pn, 1)
            end = start + relativedelta(months=1) - relativedelta(days=1)
            return start, end

        if pt == "week":
            start = date.fromisocalendar(y, pn, 1)
            end = start + relativedelta(days=6)
            return start, end

        raise ValueError(
            f"{pt} is not a valid option. Please choose one of: {self.VALID_PERIOD_TYPES}."
        )

    @staticmethod
    def _add_wait_period(d: date, months: int, days: int, *, boundary: str) -> date:
        """Boundary-aware offset of a date by a wait period.

        For `boundary="start"` -> just add months and days (relativedelta handles rollovers).
        For `boundary="end"`   -> add months, snap to end of that month, then add days.

        Args:
            d: The base date to offset.
            months: Number of months to add.
            days: Number of days to add after the month offset.
            boundary: Either `start` or `end` to specify boundary-logic.

        Returns:
            Offset date.

        Raises:
            ValueError: If `boundary` is not as expected.
        """
        if boundary == "start":
            return d + relativedelta(months=months, days=days)
        elif boundary == "end":
            if months == 0:
                return d + relativedelta(days=days)
            added_months = d + relativedelta(months=months)
            last_day_of_month = calendar.monthrange(
                added_months.year, added_months.month
            )[1]
            return added_months.replace(day=last_day_of_month) + relativedelta(
                days=days
            )
        raise ValueError("boundary must be 'start' or 'end'.")

    @property
    def etterslep_window(self) -> tuple[date, date]:
        """Computes the wait-period-adjusted calendar window.

        Returns:
            A `(etterslep_start, etterslep_end)` tuple of offset dates.
        """
        start, end = self.window

        etterslep_start = self._add_wait_period(
            start, self.wait_months, self.wait_days, boundary="start"
        )
        etterslep_end = self._add_wait_period(
            end, self.wait_months, self.wait_days, boundary="end"
        )
        return etterslep_start, etterslep_end

    # --------------------------------------------------------------------
    # Methods
    # --------------------------------------------------------------------
    def to_query_params(self) -> dict[str, date]:
        """Returns a dict for parameterising SQL queries in event extraction.

        Returns:
            A dictionary with four `date` values:

            - `"start_date"`: First day of the period.
            - `"end_date"`: Last day of the period.
            - `"etterslep_start"`: Wait-period-adjusted start date.
            - `"etterslep_end"`: Wait-period-adjusted end date.
        """
        start_date, end_date = self.window
        etterslep_start, etterslep_end = self.etterslep_window

        return {
            "start_date": start_date,
            "end_date": end_date,
            "etterslep_start": etterslep_start,
            "etterslep_end": etterslep_end,
        }
