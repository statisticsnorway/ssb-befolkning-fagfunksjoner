# Befolkning Fagfunksjoner

[![PyPI](https://img.shields.io/pypi/v/ssb-befolkning-fagfunksjoner.svg)][pypi status]
[![Status](https://img.shields.io/pypi/status/ssb-befolkning-fagfunksjoner.svg)][pypi status]
[![Python Version](https://img.shields.io/pypi/pyversions/ssb-befolkning-fagfunksjoner)][pypi status]
[![License](https://img.shields.io/pypi/l/ssb-befolkning-fagfunksjoner)][license]

[![Documentation](https://github.com/statisticsnorway/ssb-befolkning-fagfunksjoner/actions/workflows/docs.yml/badge.svg)][documentation]
[![Tests](https://github.com/statisticsnorway/ssb-befolkning-fagfunksjoner/actions/workflows/tests.yml/badge.svg)][tests]
[![Coverage](https://sonarcloud.io/api/project_badges/measure?project=statisticsnorway_ssb-befolkning-fagfunksjoner&metric=coverage)][sonarcov]
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=statisticsnorway_ssb-befolkning-fagfunksjoner&metric=alert_status)][sonarquality]

[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)][pre-commit]
[![Black](https://img.shields.io/badge/code%20style-black-000000.svg)][black]
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Poetry](https://img.shields.io/endpoint?url=https://python-poetry.org/badge/v0.json)][poetry]

[pypi status]: https://pypi.org/project/ssb-befolkning-fagfunksjoner/
[documentation]: https://statisticsnorway.github.io/ssb-befolkning-fagfunksjoner
[tests]: https://github.com/statisticsnorway/ssb-befolkning-fagfunksjoner/actions?workflow=Tests
[sonarcov]: https://sonarcloud.io/summary/overall?id=statisticsnorway_ssb-befolkning-fagfunksjoner
[sonarquality]: https://sonarcloud.io/summary/overall?id=statisticsnorway_ssb-befolkning-fagfunksjoner
[pre-commit]: https://github.com/pre-commit/pre-commit
[black]: https://github.com/psf/black
[poetry]: https://python-poetry.org/

Collection of python functions used in statistics production in the Division for Population Statistics at Statistics Norway.

## Features

- TODO

## Requirements

- TODO

## Installation
```bash
poetry add ssb-befolkning-fagfunksjoner
```

## Usage

### EventParams
`EventParams` contains logic for:
- Prompting and validating parameters for event periods
- Creating period labels
- Computing calendar window for the chosen period
- Exposing event parameters for parameterising SQL queries

Supported period types are:
- `year`
- `halfyear` (1-2)
- `quarter` (1-4)
- `month` (1-12)
- `week` (ISO week, 1-53)

The class can be constructed with explicit arguments in code:
```python
from ssb_befolkning_fagfunksjoner import EventParams

# Example: March 2024, with default wait period (1 month, 0 days)
params = EventParams(
    year=2024,
    period_type="month",
    period_number=3,
    specify_wait_period=False,  # default; can be omitted
)
```

If input arguments are omitted, the user will be prompted:
- `year`: prompts for an integer between 1900 and current year
- `period_type`: prompts for a valid period type
    - Accepts both full names (`"quarter"`, `"month"`, etc.) and single-letter abbreviations (`"q"`, `"m"`, etc.)
- `period_number`: prompted only when needed, with appropriate range checks (e.g. 1-12 for months)
```python
from ssb_befolkning_fagfunksjoner import EventParams

# Will ask the user for missing values in the terminal
params = EventParams()
```

Once the class is constructed, get the period label as follows:
```python
# Example: March 2024, with default wait period
period_label = params.period_label
# "p2024-03"
```

Get the start and end dates of the period using the window property:
```python
# Example: March 2024, with default wait period
start_date, end_date = params.window
# datetime.date(2024, 3, 1), datetime.date(2024, 3, 31)
```

Get a dict used for parameterising SQL-queries:
```python
sql_param = params.to_query_params()
# {
#   "start_date": datetime.date(2024, 3, 1),
#   "end_date": datetime.date(2024, 3, 31),
#   "etterslep_start": datetime.date(2024, 4, 1),
#   "etterslep_end": datetime.date(2024, 4, 30)
# }
```


### Demographics

### KLASS utils

### Kommnr

## Contributing

Contributions are very welcome.
To learn more, see the [Contributor Guide].

## License

Distributed under the terms of the [MIT license][license],
_Befolkning Fagfunksjoner_ is free and open source software.

## Issues

If you encounter any problems,
please [file an issue] along with a detailed description.

## Credits

This project was generated from [Statistics Norway]'s [SSB PyPI Template].

[statistics norway]: https://www.ssb.no/en
[pypi]: https://pypi.org/
[ssb pypi template]: https://github.com/statisticsnorway/ssb-pypitemplate
[file an issue]: https://github.com/statisticsnorway/ssb-befolkning-fagfunksjoner/issues
[pip]: https://pip.pypa.io/

<!-- github-only -->

[license]: https://github.com/statisticsnorway/ssb-befolkning-fagfunksjoner/blob/main/LICENSE
[contributor guide]: https://github.com/statisticsnorway/ssb-befolkning-fagfunksjoner/blob/main/CONTRIBUTING.md
[reference guide]: https://statisticsnorway.github.io/ssb-befolkning-fagfunksjoner/reference.html
