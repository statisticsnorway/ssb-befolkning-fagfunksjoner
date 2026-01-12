import calendar
from datetime import date
from typing import Literal
from typing import Self
from typing import TypeAlias

from dateutil.relativedelta import relativedelta
from typing_extensions import TypeIs

PeriodType: TypeAlias = Literal["year", "halfyear", "quarter", "month", "week"]


class EventParams:
    """Class for handling event periods.

    - Prompts and validates event periods
    - Creates period labels (Dapla-standard)
    - Computes calendar windows for period
    - Exposes event parameters for parameterising SQL queries
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
        """Initialise an EventParams instance."""
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
        """Prompt user for missing input arguments."""
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
        """Returns TRUE if 'value' is in VALID_PERIOD_TYPES."""
        return value in cls.VALID_PERIOD_TYPES

    @classmethod
    def _prompt_etterslep_values(cls: type[Self]) -> tuple[int, int]:
        """Prompt user for wait period values."""
        wait_months = cls._prompt_int_in_range("Enter wait months")
        wait_days = cls._prompt_int_in_range("Enter wait days")

        return wait_months, wait_days

    @classmethod
    def _prompt_period_type(cls: type[Self], msg: str) -> PeriodType:
        """Prompt user for period type, with instant validity feedback.

        Accepts full names and single-letter abbreviations (e.g., 'q' → 'quarter').
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
        """Prompt user for a valid integer within a range, with immediate feedback."""
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
        """Prompt user for valid year between 1900 and current year, with instant feedback."""
        current_year = date.today().year
        return cls._prompt_int_in_range("Enter year", (1900, current_year))

    # --------------------------------------------------------------------
    # Properties
    # --------------------------------------------------------------------
    @property
    def period_label(self) -> str:
        """Returns a period label string formatted to Dapla standard."""
        if self.period_type == "year":
            return f"p{self.year}"

        if self.period_type == "halfyear":
            return f"p{self.year}-H{self.period_number}"

        if self.period_type == "quarter":
            return f"p{self.year}-Q{self.period_number}"

        if self.period_type == "month":
            return f"p{self.year}-{str(self.period_number).zfill(2)}"

        if self.period_type == "week":
            return f"p{self.year}-W{str(self.period_number).zfill(2)}"

        raise ValueError()

    @property
    def etterslep_label(self) -> str:
        """Returns a wait period label string formatted like: '1m0d'.

        Defaults to '1m0d' if specify_wait_period' is False.
        """
        return f"{self.wait_months}m{self.wait_days}d"

    @property
    def window(self) -> tuple[date, date]:
        """Returns the start date and end date for the given period, as a tuple.

        Both dates are within the period, so 'end_date' is the last day of the period. E.g. end of the month.
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
        """Add months and days to given date with boundary-aware logic.

        - boundary = 'start' -> just add months and days (relativedelta handles rollovers).
        - boundary = 'end'   -> add months, snap to end of that month, then add days.
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
        """Returns the start date and end date for the wait period.

        Calculated by taking the start and end dates and adding the wait period to each.
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
        """Returns a dict for parameterising SQL queries."""
        start_date, end_date = self.window
        etterslep_start, etterslep_end = self.etterslep_window

        return {
            "start_date": start_date,
            "end_date": end_date,
            "etterslep_start": etterslep_start,
            "etterslep_end": etterslep_end,
        }
