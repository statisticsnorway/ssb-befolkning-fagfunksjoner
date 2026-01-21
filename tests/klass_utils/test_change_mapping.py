import datetime
from itertools import pairwise
from unittest.mock import Mock

import klass
import networkx
import pandas as pd
import pytest
from klass.requests.klass_types import CorrespondenceTablesType
from klass.requests.klass_types import VersionPartType

from ssb_befolkning_fagfunksjoner.klass_utils.change_mapping import _build_change_graph
from ssb_befolkning_fagfunksjoner.klass_utils.change_mapping import _CessionType
from ssb_befolkning_fagfunksjoner.klass_utils.change_mapping import _CodePoint
from ssb_befolkning_fagfunksjoner.klass_utils.change_mapping import (
    get_klass_change_mapping,
)


@pytest.fixture()
def classification_mocker() -> Mock:
    classification_mocker = Mock(spec=klass.KlassClassification)
    versions_meta: list[VersionPartType] = [
        {
            "name": "Kommuneinndeling 2026",
            "version_id": 5,
            "validFrom": "2026-01-01",
        },
        {
            "name": "Kommuneinndeling 2024",
            "version_id": 4,
            "validFrom": "2024-01-01",
            "validTo": "2026-01-01",
        },
        {
            "name": "Kommuneinndeling 2023",
            "version_id": 3,
            "validFrom": "2023-01-01",
            "validTo": "2024-01-01",
        },
        {
            "name": "Kommuneinndeling 2019",
            "version_id": 1,
            "validFrom": "2019-01-01",
            "validTo": "2020-01-01",
        },
        {
            "name": "Kommuneinndeling 2020",
            "version_id": 2,
            "validFrom": "2020-01-01",
            "validTo": "2022-01-01",
        },
    ]  # pyright: ignore[reportAssignmentType]
    classification_mocker.versions = versions_meta

    change_meta: list[CorrespondenceTablesType] = [
        {
            "name": "Kommuneinndeling 2026 - Kommuneinndeling 2024",
            "id": 4,
            "source": "Kommuneinndeling 2026",
            "sourceId": 5,
            "target": "Kommuneinndeling 2024",
            "targetId": 4,
        },
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

    corr_meta: list[tuple[CorrespondenceTablesType, ...]] = [
        (change_meta[0],),
        *pairwise(change_meta),
        (change_meta[-1],),
    ]

    versions_codes: list[list[dict[str, str]]] = [
        [{"code": "3118"}, {"code": "3207"}, {"code": "3216"}],
        [
            {"code": "1508"},
            {"code": "1580"},
            {"code": "3118"},
            {"code": "3207"},
            {"code": "3216"},
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

    correspondence: list[list[dict[str, str]]] = [
        [
            {"sourceCode": "3118", "targetCode": "3118"},
            {"sourceCode": "3207", "targetCode": "3118"},
            {"sourceCode": "3207", "targetCode": "3207"},
            {"sourceCode": "3216", "targetCode": "3118"},
            {"sourceCode": "3216", "targetCode": "3216"},
        ],
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
        Mock(spec=klass.KlassCorrespondence) for _ in range(len(change_meta))
    ]

    for mock, meta, corr in zip(
        change_table_mock, change_meta, correspondence, strict=True
    ):
        mock.sourceId = meta["sourceId"]
        mock.targetId = meta["targetId"]
        mock.correspondence = corr

    change_table_mock.reverse()

    def _get_change_table(correspondence_id: int, *args, **kwargs) -> Mock:
        return change_table_mock[correspondence_id - 1]

    version_mockers: list[klass.KlassVersion] = [
        Mock(spec=klass.KlassVersion) for _ in range(len(corr_meta))
    ]

    for mock, v_id, meta, codes in zip(
        version_mockers,
        range(len(corr_meta), 0, -1),
        corr_meta,
        versions_codes,
        strict=True,
    ):
        mock.correspondenceTables = meta
        mock.classificationItems = codes
        mock.version_id = v_id
        mock.get_correspondence = _get_change_table

    version_mockers.reverse()

    def _get_version(version_id, *args, **kwargs):
        return version_mockers[version_id - 1]

    classification_mocker.get_version = _get_version

    return classification_mocker


cases = [
    (
        datetime.date(2024, 1, 1),
        datetime.date(2025, 1, 1),
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
        datetime.date(2025, 1, 1),
        pd.Series(["1507"] * 6, index=["1504", "1507", "1508", "1523", "1529", "1580"]),
    ),
    (
        datetime.date(2019, 1, 1),
        datetime.date(2025, 1, 1),
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
    (
        datetime.date(2026, 1, 1),
        None,
        pd.Series(
            [
                "3118",
                "3207",
                "3216",
            ],
            index=[
                "3118",
                "3207",
                "3216",
            ],
        ),
    ),
]


@pytest.mark.parametrize(("target_date", "to_date", "expected"), cases)
def test_get_changes_mapping(
    classification_mocker, target_date, to_date, expected
) -> None:
    result = get_klass_change_mapping(
        classification_mocker, target_date=target_date, to_date=to_date
    )
    pd.testing.assert_series_equal(expected, result, check_names=False)


cases_label_graph = [
    [(_CodePoint("1504", 1), _CodePoint("1507", 2)), _CessionType.CESSATION_WHOLE],
    [(_CodePoint("1507", 2), _CodePoint("1507", 3)), _CessionType.NO_CESSION],
    [
        (_CodePoint("1507", 3), _CodePoint("1580", 4)),
        _CessionType.CESSATION_PART_TO_NEW,
    ],
    [
        (_CodePoint("3118", 4), _CodePoint("3207", 5)),
        _CessionType.ADJUSTMENT_PART_TO_EXISTING,
    ],
    [(_CodePoint("3118", 4), _CodePoint("3118", 5)), _CessionType.BORDER_CHANGE],
]


@pytest.mark.parametrize(("edge", "expected"), cases_label_graph)
def test_label_graph(edge, expected, classification_mocker) -> None:
    result = _build_change_graph(
        classification_mocker, from_date=datetime.date(2019, 1, 1)
    )
    get_cession_type = networkx.get_edge_attributes(result, "cession_type")

    assert get_cession_type[edge] == expected
