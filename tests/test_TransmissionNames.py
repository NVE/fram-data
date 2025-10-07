import re
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest
from pandera.errors import SchemaError, SchemaErrors

from framdata.database_names.TransmissionNames import (
    TransmissionMetadataSchema,
    TransmissionNames,
    TransmissionSchema,
)

TRANSMISSION_COLUMNS = [
    "TransmissionID",
    "FromNode",
    "ToNode",
    "Capacity",
    "Loss",
    "Tariff",
    "MaxOperationalBound",
    "MinOperationalBound",
    "RampUp",
    "RampDown",
]


@patch("framdata.database_names.TransmissionNames.Transmission", new_callable=MagicMock)
def test_create_component(mock_transmission: MagicMock) -> None:
    mock_transmission_instance = MagicMock()
    mock_transmission.return_value = mock_transmission_instance

    TransmissionNames._parse_args = MagicMock(
        return_value={
            "Capacity": "200 MW",
            "Loss": "0.01",
            "Tariff": "0.001 EUR",
            "MaxOperationalBound": "profile_ref_max",
            "MinOperationalBound": "profile_ref_min",
            "RampUp": "0.4",
            "RampDown": "0.4",
        },
    )

    TransmissionNames._add_meta = MagicMock()
    row = np.array(
        [
            "node1->node2",
            "node1",
            "node2",
            200,
            0.01,
            0.001,
            "profile_ref_max",
            "profile_ref_min",
            0.4,
            0.4,
            "membership",
        ],
        dtype=object,
    )
    indices = {
        "TransmissionID": 0,
        "FromNode": 1,
        "ToNode": 2,
        "Capacity": 3,
        "Loss": 4,
        "Tariff": 5,
        "MaxOperationalBound": 6,
        "MinOperationalBound": 7,
        "RampUp": 8,
        "RampDown": 9,
        "MemberColumn": 10,
    }
    meta_columns = {"MemberColumns"}
    meta_data = pd.DataFrame(
        [
            ["Capacity", "MW"],
            ["Loss", None],
            ["Tariff", "EUR"],
            ["MaxOperationalBound", None],
            ["MinOperationalBound", None],
            ["RampUp", None],
            ["RampDown", None],
        ],
        columns=["attribute", "unit"],
    )

    result = TransmissionNames.create_component(row, indices, meta_columns, meta_data)
    expected = {"node1->node2": mock_transmission_instance}

    assert result == expected
    mock_transmission.assert_called_once()
    TransmissionNames._add_meta.assert_called_once_with(mock_transmission_instance, row, indices, meta_columns)


def test_transmission_schema() -> None:
    valid_data = pd.DataFrame(
        data=[
            ["T1", "T1_from_node", "T1_to_node", "a", "b", "c", "d", "e", "f", "g"],
            ["T2", "T2_from_node", "T2_to_node", 1, 0.2, 3, 4, 5, None, 2],
            ["T3", "T3_from_node", "T3_to_node", 1.5, 0.25, 3.5, 4.5, 5.5, 4.0, 4.0],
            ["T4", "T4_from_node", "T4_to_node", 5.5, None, None, None, 5.5, None, None],
        ],
        columns=TRANSMISSION_COLUMNS,
    )
    TransmissionSchema.validate(valid_data)


def test_transmission_schema_transmisson_id_not_unique() -> None:
    invalid_data = pd.DataFrame(
        [
            ["T1", "T1_from_node", "T1_to_node", "a", "b", "c", "d", "e", "f", "g"],
            ["T1", "T2_from_node", "T2_to_node", "a", "b", "c", "d", "e", "f", "g"],
        ],
        columns=TRANSMISSION_COLUMNS,
    )
    with pytest.raises(SchemaError, match="series 'TransmissionID' contains duplicate values"):
        TransmissionSchema.validate(invalid_data, lazy=False)


def test_transmission_schema_transmission_id_require_str() -> None:
    invalid_data = pd.DataFrame(
        [
            [1, "T1_from_node", "T1_to_node", "a", "b", "c", "d", "e", "f", "g"],
            [2.0, "T2_from_node", "T2_to_node", "a", "b", "c", "d", "e", "f", "g"],
            [False, "T3_from_node", "T3_to_node", "a", "b", "c", "d", "e", "f", "g"],
        ],
        columns=TRANSMISSION_COLUMNS,
    )
    with pytest.raises(SchemaErrors, match="expected series 'TransmissionID' to have type str"):
        TransmissionSchema.validate(invalid_data, lazy=True)


def test_transmission_schema_from_node_require_str() -> None:
    invalid_data = pd.DataFrame(
        [
            ["T1", 1, "T1_to_node", "a", "b", "c", "d", "e", "f", "g"],
            ["T2", 2.0, "T2_to_node", "a", "b", "c", "d", "e", "f", "g"],
            ["T3", False, "T3_to_node", "a", "b", "c", "d", "e", "f", "g"],
        ],
        columns=TRANSMISSION_COLUMNS,
    )
    with pytest.raises(SchemaErrors, match="expected series 'FromNode' to have type str"):
        TransmissionSchema.validate(invalid_data, lazy=True)


def test_transmission_schema_to_node_require_str() -> None:
    invalid_data = pd.DataFrame(
        [
            ["T1", "T1_from_node", 1, "a", "b", "c", "d", "e", "f", "g"],
            ["T2", "T2_from_node", 2.0, "a", "b", "c", "d", "e", "f", "g"],
            ["T3", "T3_from_node", False, "a", "b", "c", "d", "e", "f", "g"],
        ],
        columns=TRANSMISSION_COLUMNS,
    )
    with pytest.raises(SchemaErrors, match="expected series 'ToNode' to have type str"):
        TransmissionSchema.validate(invalid_data, lazy=True)


def test_transmission_schema_transmission_id_non_nullable() -> None:
    invalid_data = pd.DataFrame(
        [
            [None, "T1_from_node", "T1_to_node", "a", "b", "c", "d", "e", "f", "g"],
        ],
        columns=TRANSMISSION_COLUMNS,
    )
    with pytest.raises(SchemaError, match="non-nullable series 'TransmissionID' contains null values"):
        TransmissionSchema.validate(invalid_data, lazy=False)


def test_transmission_schema_from_node_non_nullable() -> None:
    invalid_data = pd.DataFrame(
        [
            ["T1", None, "T1_to_node", "a", "b", "c", "d", "e", "f", "g"],
        ],
        columns=TRANSMISSION_COLUMNS,
    )
    with pytest.raises(SchemaError, match="non-nullable series 'FromNode' contains null values"):
        TransmissionSchema.validate(invalid_data, lazy=False)


def test_transmission_schema_to_node_non_nullable() -> None:
    invalid_data = pd.DataFrame(
        [
            ["T1", "T1_from_node", None, "a", "b", "c", "d", "e", "f", "g"],
        ],
        columns=TRANSMISSION_COLUMNS,
    )
    with pytest.raises(SchemaError, match="non-nullable series 'ToNode' contains null values"):
        TransmissionSchema.validate(invalid_data, lazy=False)


def test_transmission_schema_capacity_non_nullable() -> None:
    invalid_data = pd.DataFrame(
        [
            ["T1", "T1_from_node", "T1_to_node", None, "b", "c", "d", "e", "f", "g"],
        ],
        columns=TRANSMISSION_COLUMNS,
    )
    with pytest.raises(SchemaError, match="non-nullable series 'Capacity' contains null values"):
        TransmissionSchema.validate(invalid_data, lazy=False)


def test_transmission_schema_capacity_less_than_zero() -> None:
    invalid_data = pd.DataFrame(
        [
            ["T1", "T1_from_node", "T1_to_node", -1, "b", "c", "d", "e", "f", "g"],
        ],
        columns=TRANSMISSION_COLUMNS,
    )
    with pytest.raises(SchemaError, match=re.escape("<Check numeric_values_greater_than_or_equal_to_0>")):
        TransmissionSchema.validate(invalid_data)


def test_transmission_schema_internal_line_error() -> None:
    invalid_data = pd.DataFrame(
        [
            ["T1", "T1_from_node", "T1_to_node", 100, "b", "c", "d", "e", "f", "g"],
            ["T2", "T2_from_node", "T2_from_node", 200, "b", "c", "d", "e", "f", "g"],
        ],
        columns=TRANSMISSION_COLUMNS,
    )
    with pytest.raises(SchemaError, match="<Check check_internal_line_error>"):
        TransmissionSchema.validate(invalid_data, lazy=False)


def test_transmission_meta_data_schema() -> None:
    valid_data = pd.DataFrame(
        [
            ["TransmissionID", None, None, None, "Unique transmission ID.", None, None, None, None],
            ["Capacity", "float", "Transmission.Grid.capacity", "MW", None, True, None, None, None],
        ],
        columns=[
            "Attribute",
            "Dtype",
            "Reference",
            "Unit",
            "Description",
            "IsMaxLevel",
            "IsZeroOneProfile",
            "RefPeriodStartYear",
            "RefPeriodNumberOfYears",
        ],
    )
    TransmissionMetadataSchema.validate(valid_data)


def test_transmission_meta_data_schema_check_capacity_unit() -> None:
    invalid_data = pd.DataFrame(
        [
            ["TransmissionID", None, None, None, "", None, None, None, None],
            ["Capacity", "float", "Transmission.Grid.capacity", 1, "", True, None, None, None],
        ],
        columns=[
            "Attribute",
            "Dtype",
            "Reference",
            "Unit",
            "Description",
            "IsMaxLevel",
            "IsZeroOneProfile",
            "RefPeriodStartYear",
            "RefPeriodNumberOfYears",
        ],
    )
    with pytest.raises(SchemaError, match=re.escape("expected series 'Unit' to have type str")):
        TransmissionMetadataSchema.validate(invalid_data, lazy=False)
