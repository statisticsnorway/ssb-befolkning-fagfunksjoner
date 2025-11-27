import datetime
from unittest.mock import Mock

import klass
import pandas as pd
import pytest
from klass.requests.klass_types import VersionPartType

from ssb_befolkning_fagfunksjoner.klass_utils.level_mapping import aggregate_codes
from ssb_befolkning_fagfunksjoner.klass_utils.level_mapping import get_klass_level_map


@pytest.fixture()
def version_nuts2024_mocker() -> Mock:
    nuts_2024_mock = Mock(spec=klass.KlassVersion)

    levels = [
        {"levelNumber": 1, "levelName": "NUTS 2"},
        {"levelNumber": 2, "levelName": "NUTS 3"},
        {"levelNumber": 3, "levelName": "LAU"},
    ]

    code_items = [
        {
            "code": "0301",
            "parentCode": "NO081",
            "level": "3",
            "name": "Oslo",
        },
        {
            "code": "NO081",
            "parentCode": "NO08",
            "level": "2",
            "name": "Oslo",
        },
        {
            "code": "NO08",
            "parentCode": "",
            "level": "1",
            "name": "Oslo og Viken",
        },
        {
            "code": "3401",
            "parentCode": "NO020",
            "level": "3",
            "name": "Kongsvinger",
        },
        {
            "code": "3415",
            "parentCode": "NO020",
            "level": "3",
            "name": "Sør-Odal",
        },
        {
            "code": "NO020",
            "parentCode": "NO02",
            "level": "2",
            "name": "Innlandet",
        },
        {
            "code": "NO02",
            "parentCode": "",
            "level": "1",
            "name": "Innlandet",
        },
    ]

    nuts_2024_mock.data = pd.DataFrame.from_records(code_items)
    nuts_2024_mock.levels = levels

    return nuts_2024_mock


@pytest.fixture()
def classification_levels_mocker(version_nuts2024_mocker: Mock) -> Mock:
    classification_mocker = Mock(spec=klass.KlassClassification)
    versions_meta: list[VersionPartType] = [
        {
            "name": "NUTS 2024",
            "version_id": 2482,
            "validFrom": "2024-01-01",
        },
        {
            "name": "NUTS 2023",
            "version_id": 3176,
            "validFrom": "2023-01-01",
            "validTo": "2024-01-01",
        },
    ]  # pyright: ignore[reportAssignmentType]

    def _get_version(version_id, *args, **kwargs):
        if version_id != 2482:
            raise KeyError

        return version_nuts2024_mocker

    classification_mocker.versions = versions_meta
    classification_mocker.get_version = _get_version

    return classification_mocker


expected_level_2 = pd.Series(
    ["NO081", "NO020", "NO020", "NO020", "NO081"],
    index=pd.Index(["0301", "3401", "3415", "NO020", "NO081"]),
)
expected_level_1 = pd.Series(
    ["NO08", "NO02", "NO02", "NO02", "NO02", "NO08", "NO08"],
    index=pd.Index(["0301", "3401", "3415", "NO02", "NO020", "NO08", "NO081"]),
)

test_cases_mapping = [
    (2, expected_level_2),
    ("NUTS 3", expected_level_2),
    (1, expected_level_1),
    ("1", expected_level_1),
]

test_labels_mapping = [
    "nuts3_as_index",
    "nuts3_as_label",
    "nuts2_as_int_index",
    "nuts2_as_str_index",
]


@pytest.mark.parametrize(
    ("level_index_or_label", "expected_mapping"),
    test_cases_mapping,
    ids=test_labels_mapping,
)
def test_level_map_with_version(
    level_index_or_label: str | int,
    expected_mapping: pd.Series,
    version_nuts2024_mocker: Mock,
):
    mapping = get_klass_level_map(level_index_or_label, version=version_nuts2024_mocker)
    pd.testing.assert_series_equal(mapping, expected_mapping, check_names=False)


@pytest.mark.parametrize(
    ("level_index_or_label", "expected_mapping"),
    test_cases_mapping,
    ids=test_labels_mapping,
)
def test_level_map_with_classifcation(
    level_index_or_label: str | int,
    expected_mapping: pd.Series,
    classification_levels_mocker: Mock,
):
    mapping = get_klass_level_map(
        level_index_or_label,
        classification=classification_levels_mocker,
        date=datetime.date(2024, 1, 1),
    )
    pd.testing.assert_series_equal(mapping, expected_mapping, check_names=False)


invalid_level = [
    ("LAU 1", r"^LAU 1 is not a valid label in the Klass version\."),
    (4, r"^Klass version don't have a level with index 4\."),
    ("4", r"^Klass version don't have a level with index 4\."),
]


@pytest.mark.parametrize(
    ("level_index_or_label", "expected_error_msg"),
    invalid_level,
    ids=["label", "index_as_int", "index_as_string"],
)
def test_invalid_level(
    level_index_or_label: str | int,
    expected_error_msg: str,
    classification_levels_mocker: Mock,
):
    with pytest.raises(ValueError, match=expected_error_msg):
        get_klass_level_map(
            level_index_or_label,
            classification=classification_levels_mocker,
            date=datetime.date(2024, 1, 1),
        )


test_cases_aggregate = [
    (
        2,
        pd.Series(["0301", "3401", "3415"], name="nuts"),
        pd.Series(["NO081", "NO020", "NO020"], name="nuts_3"),
        False,
    ),
    (
        1,
        pd.Series(["0301", "3401", "3415"], name="nuts"),
        pd.Series(["NO08", "NO02", "NO02"], name="nuts_2"),
        False,
    ),
    (
        1,
        pd.Series(["0301", "3401", "zz1"], name="nuts"),
        pd.Series(["NO08", "NO02", pd.NA], name="nuts_2"),
        False,
    ),
    (
        1,
        pd.Series(["0301", "3401", "zz1"], name="nuts"),
        pd.Series(["NO08", "NO02", "zz1"], name="nuts_2"),
        True,
    ),
]


@pytest.mark.parametrize(
    ("level", "series", "expected_agg", "keep_others"),
    test_cases_aggregate,
    ids=["nuts_3", "nuts_2", "filter_unknown", "pass-through_unknown"],
)
def test_aggregate(
    level: int,
    series: pd.Series,
    expected_agg: pd.Series,
    keep_others: bool,
    classification_levels_mocker: Mock,
):
    aggregated = aggregate_codes(
        series,
        level,
        classification=classification_levels_mocker,
        date=datetime.date(2024, 1, 1),
        keep_others=keep_others,
    )
    pd.testing.assert_series_equal(aggregated, expected_agg)
