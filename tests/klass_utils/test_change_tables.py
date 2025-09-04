import datetime
from klass import KlassClassification, KlassCorrespondence, KlassVersion
import pandas as pd
import pytest
from unittest.mock import Mock

from klass.requests.klass_types import CorrespondenceTablesType, VersionPartType

from ssb_befolkning_fagfunksjoner.klass_utils.loaders import get_changes_mapping


@pytest.fixture()
def classification_mocker():
    classification_mocker = Mock(spec=KlassClassification)
    versions_meta: list[VersionPartType] = [
        {
            "name": "Kommuneinndeling 2024",
            "version_id": 4,
            "validFrom": "2024-01-01",
        },
        {
            "name": "Kommuneinndeling 2023",
            "version_id": 3,
            "validFrom": "2023-01-01",
            "validTo": "2024-01-01",
        },
        {
            "name": "Kommuneinndeling 2020",
            "version_id": 2,
            "validFrom": "2020-01-01",
            "validTo": "2022-01-01",
        },
        {
            "name": "Kommuneinndeling 2019",
            "version_id": 1,
            "validFrom": "2019-01-01",
            "validTo": "2020-01-01",
        },
    ]  # pyright: ignore[reportAssignmentType]
    classification_mocker.versions = versions_meta

    change_meta: list[CorrespondenceTablesType] = [
        {
            "name": "Kommuneinndeling 2024 - Kommuneinndeling 2023",
            "id": 3,
            "source": "Kommuneinndeling 2024",
            "sourceId": 4,
            "target": "Kommuneinndeling 2023",
            "targetId": 3,
        },
        {
            "name": "Kommuneinndeling 2023 - Kommuneinndeling 2020",
            "id": 2,
            "source": "Kommuneinndeling 2023",
            "sourceId": 3,
            "target": "Kommuneinndeling 2020",
            "targetId": 2,
        },
        {
            "name": "Kommuneinndeling 2020 - Kommuneinndeling 2019",
            "id": 1,
            "source": "Kommuneinndeling 2022",
            "sourceId": 2,
            "target": "Kommuneinndeling 2021",
            "targetId": 1,
        },
    ]  # pyright: ignore[reportAssignmentType]

    corr_meta: list[list[CorrespondenceTablesType]] = [
        [change_meta[0]],
        [change_meta[0], change_meta[1]],
        [change_meta[1], change_meta[2]],
        [change_meta[2]],
    ]

    versions_codes: list[list[dict]] = [
        [
            {"code": "1508"},
            {"code": "1580"},
        ],
        [
            {"code": "1507"},
        ],
        [
            {"code": "1507"},
        ],
        [
            {"code": "1504"},
            {"code": "1523"},
            {"code": "1529"},
        ],
    ]

    correspondence: list[list[dict]] = [
        [
            {"sourceCode": "1508", "targetCode": "1507"},
            {"sourceCode": "1580", "targetCode": "1507"},
        ],
        [],
        [
            {"sourceCode": "1507", "targetCode": "1504"},
            {"sourceCode": "1507", "targetCode": "1523"},
            {"sourceCode": "1507", "targetCode": "1529"},
        ],
    ]

    change_table_mock = [
        Mock(spec=KlassCorrespondence) for _ in range(len(change_meta))
    ]

    for mock, meta, corr in zip(
        change_table_mock, change_meta, correspondence, strict=True
    ):
        mock.sourceId = meta["sourceId"]
        mock.targetId = meta["targetId"]
        mock.correspondence = corr

    def _get_change_table(correspondence_id, *args, **kwargs):
        return change_table_mock[correspondence_id - 1]

    version_mockers: list[KlassVersion] = [
        Mock(spec=KlassVersion) for _ in range(len(corr_meta))
    ]

    for mock, v_id, meta, codes in zip(
        version_mockers, range(4, 0, -1), corr_meta, versions_codes, strict=True
    ):
        mock.correspondenceTables = meta
        mock.classificationItems = codes
        mock.version_id = v_id
        mock.get_correspondence = _get_change_table

    def _get_version(version_id, *args, **kwargs):
        return version_mockers[version_id - 1]

    classification_mocker.get_version = _get_version

    return classification_mocker


cases = [
    (
        datetime.date(2024, 1, 1),
        pd.Series(
            [
                "1508",
                "1580",
                "1508",
                "1580",
                "1508",
                "1508",
                "1580",
                "1508",
                "1580",
                "1580",
            ],
            index=[
                "1504",
                "1504",
                "1507",
                "1507",
                "1508",
                "1523",
                "1523",
                "1529",
                "1529",
                "1580",
            ],
        ),
    ),
    (
        datetime.date(2023, 1, 1),
        pd.Series(["1507"] * 6, index=["1504", "1507", "1508", "1523", "1529", "1580"]),
    ),
    (
        datetime.date(2019, 1, 1),
        pd.Series(
            [
                "1504",
                "1504",
                "1523",
                "1529",
                "1504",
                "1523",
                "1529",
                "1523",
                "1529",
                "1504",
                "1523",
                "1529",
            ],
            index=[
                "1504",
                "1507",
                "1507",
                "1507",
                "1508",
                "1508",
                "1508",
                "1523",
                "1529",
                "1580",
                "1580",
                "1580",
            ],
        ),
    ),


]


@pytest.mark.parametrize("target_date, expected", cases)
def test_get_changes_mapping(classification_mocker, target_date, expected):
    result = get_changes_mapping(classification_mocker, target_date=target_date)
    pd.testing.assert_series_equal(expected, result, check_names=False)
