import re
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest
from pandera.errors import SchemaError, SchemaErrors

from framdata.database_names.DemandNames import DemandMetadataSchema, DemandNames, DemandSchema


@patch("framdata.database_names.DemandNames.Demand", new_callable=MagicMock)
def test_create_component(mock_demand: MagicMock) -> None:
    row = np.array(
        ["id", "node", 2000, None, None, None, None, "profile_ref", "temp_profile_ref", 300, "building"],
        dtype=object,
    )
    indices = {
        "ConsumerID": 0,
        "PowerNode": 1,
        "ReservePrice": 2,
        "PriceElasticity": 3,
        "MinPriceLimit": 4,
        "MaxPriceLimit": 5,
        "NormalPrice": 6,
        "CapacityProfile": 7,
        "TemperatureProfile": 8,
        "Capacity": 9,
        "Category": 10,
    }

    meta_columns = ["Category"]
    meta_data = pd.DataFrame(
        [
            ["ConsumerID", None],
            ["PowerNode", None],
            ["ReservePrice", "EUR/MWh"],
            ["PriceElasticity", None],
            ["MinPriceLimit", "EUR/MWh"],
            ["MaxPriceLimit", "EUR/MWh"],
            ["NormalPrice", "EUR/MWh"],
            ["CapacityProfile", None],
            ["TemperatureProfile", None],
            ["Capacity", "MW"],
        ],
        columns=["attribute", "unit"],
    )

    DemandNames._parse_args = MagicMock(
        return_value={
            "ReservePrice": "2000 EUR/MWh",
            "CapacityProfile": "profile_ref",
            "TemperatureProfile": "temp_profile_ref",
            "Capacity": "300 MW",
            "PriceElasticity": None,
            "MinPriceLimit": None,
            "MaxPriceLimit": None,
            "NormalPrice": None,
        },
    )
    DemandNames._add_meta = MagicMock()
    mock_demand_instance = MagicMock()
    mock_demand.return_value = mock_demand_instance

    result = DemandNames.create_component(row, indices, meta_columns, meta_data)
    expected = {"id": mock_demand_instance}

    assert result == expected
    mock_demand.assert_called_once()
    DemandNames._parse_args.assert_called_once_with(
        row,
        indices,
        [
            "ReservePrice",
            "CapacityProfile",
            "TemperatureProfile",
            "Capacity",
            "PriceElasticity",
            "MinPriceLimit",
            "MaxPriceLimit",
            "NormalPrice",
        ],
        meta_data,
    )
    DemandNames._add_meta.assert_called_once_with(mock_demand_instance, row, indices, meta_columns)


@patch("framdata.database_names.DemandNames.ElasticDemand", new_callable=MagicMock)
@patch("framdata.database_names.DemandNames.Demand", new_callable=MagicMock)
def test_create_component_with_elastic_demand(mock_demand: MagicMock, mock_elastic_demand: MagicMock) -> None:
    row = np.array(
        ["id", "node", None, -0.025, 7, 900, "normal_price_ref", "profile_ref", "temp_profile_ref", 300, "building"],
        dtype=object,
    )
    indices = {
        "ConsumerID": 0,
        "PowerNode": 1,
        "ReservePrice": 2,
        "PriceElasticity": 3,
        "MinPriceLimit": 4,
        "MaxPriceLimit": 5,
        "NormalPrice": 6,
        "CapacityProfile": 7,
        "TemperatureProfile": 8,
        "Capacity": 9,
        "Category": 10,
    }

    meta_columns = ["Category"]
    meta_data = pd.DataFrame(
        [
            ["ConsumerID", None],
            ["PowerNode", None],
            ["ReservePrice", "EUR/MWh"],
            ["PriceElasticity", None],
            ["MinPriceLimit", "EUR/MWh"],
            ["MaxPriceLimit", "EUR/MWh"],
            ["NormalPrice", "EUR/MWh"],
            ["CapacityProfile", None],
            ["TemperatureProfile", None],
            ["Capacity", "MW"],
        ],
        columns=["attribute", "unit"],
    )

    DemandNames._parse_args = MagicMock(
        return_value={
            "ReservePrice": None,
            "CapacityProfile": "profile_ref",
            "TemperatureProfile": "temp_profile_ref",
            "Capacity": "300 MW",
            "PriceElasticity": "-0.025",
            "MinPriceLimit": "7 EUR/MWh",
            "MaxPriceLimit": "900 EUR/MWh",
            "NormalPrice": "normal_price_ref",
        },
    )
    DemandNames._add_meta = MagicMock()
    mock_demand_instance = MagicMock()
    mock_demand.return_value = mock_demand_instance
    mock_elastic_demand_instance = MagicMock()
    mock_elastic_demand.return_value = mock_elastic_demand_instance

    result = DemandNames.create_component(row, indices, meta_columns, meta_data)
    expected = {"id": mock_demand_instance}

    assert result == expected
    mock_demand.assert_called_once()
    DemandNames._parse_args.assert_called_once_with(
        row,
        indices,
        [
            "ReservePrice",
            "CapacityProfile",
            "TemperatureProfile",
            "Capacity",
            "PriceElasticity",
            "MinPriceLimit",
            "MaxPriceLimit",
            "NormalPrice",
        ],
        meta_data,
    )
    DemandNames._add_meta.assert_called_once_with(mock_demand_instance, row, indices, meta_columns)


def test_demand_schema() -> None:
    valid_data = pd.DataFrame(
        [
            ["NO1", "NO1_node", "1", "2", "3", "4", "5", "6", "7", "8", "9"],
            ["NO2", "NO2_node", 100, -200, 300, 400, 500, 1, 700, 800, 900],
            ["NO3", "NO3_node", 1.5, -2.5, 3.5, 4.5, 5.5, 0.6, 7.7, 8.8, 9.9],
            ["NO4", "NO4_node", None, None, None, None, None, None, None, "8", None],
        ],
        columns=[
            "ConsumerID",
            "PowerNode",
            "ReservePrice",  # 1
            "PriceElasticity",  # 2
            "MinPriceLimit",  # 3
            "MaxPriceLimit",  # 4
            "NormalPrice",  # 5
            "CapacityProfile",  # 6
            "TemperatureProfile",  # 7
            "Capacity",  # 8
            "OptionalMetaColumn",  # 9
        ],
    )
    DemandSchema.validate(valid_data, lazy=True)


def test_demand_schema_check_elastic_demand() -> None:
    valid_data = pd.DataFrame(
        [
            ["NO1", "NO1_node", "1", "2", "3", "4", "5", "6", "7", "8", "9"],
            ["NO2", "NO2_node", 100, None, None, None, None, 1, 700, 800, 900],
            ["NO3", "NO3_node", 100, -2, None, None, None, 1, 700, 800, 900],
        ],
        columns=[
            "ConsumerID",
            "PowerNode",
            "ReservePrice",  # 1
            "PriceElasticity",  # 2
            "MinPriceLimit",  # 3
            "MaxPriceLimit",  # 4
            "NormalPrice",  # 5
            "CapacityProfile",  # 6
            "TemperatureProfile",  # 7
            "Capacity",  # 8
            "OptionalMetaColumn",  # 9
        ],
    )
    with pytest.raises(SchemaError, match=re.escape("<Check check_elastic_demand>")):
        DemandSchema.validate(valid_data)


def test_demand_schema_consumer_id_not_unique() -> None:
    invalid_data = pd.DataFrame(
        [
            ["NO1", "NO1_node", "1", "2", "3", "4", "5", "6", "7", "8"],
            ["NO1", "NO2_node", 100, 200, 300, 400, 500, 600, 700, 800],
        ],
        columns=[
            "ConsumerID",
            "PowerNode",
            "ReservePrice",  # 1
            "PriceElasticity",  # 2
            "MinPriceLimit",  # 3
            "MaxPriceLimit",  # 4
            "NormalPrice",  # 5
            "CapacityProfile",  # 6
            "TemperatureProfile",  # 7
            "Capacity",  # 8
        ],
    )
    with pytest.raises(SchemaError, match="series 'ConsumerID' contains duplicate values"):
        DemandSchema.validate(invalid_data, lazy=False)


def test_demand_schema_consumer_id_require_str() -> None:
    invalid_data = pd.DataFrame(
        [
            [10000, "NO1_node", "1", "2", "3", "4", "5", "6", "7", "8"],
            [10.10, "NO2_node", 100, 200, 300, 400, 500, 600, 700, 800],
            [False, "NO3_node", 100, 200, 300, 400, 500, 600, 700, 800],
        ],
        columns=[
            "ConsumerID",
            "PowerNode",
            "ReservePrice",  # 1
            "PriceElasticity",  # 2
            "MinPriceLimit",  # 3
            "MaxPriceLimit",  # 4
            "NormalPrice",  # 5
            "CapacityProfile",  # 6
            "TemperatureProfile",  # 7
            "Capacity",  # 8
        ],
    )
    with pytest.raises(SchemaErrors, match="expected series 'ConsumerID' to have type str"):
        DemandSchema.validate(invalid_data, lazy=True)


def test_demand_schema_power_node_require_str() -> None:
    invalid_data = pd.DataFrame(
        [
            ["NO1", 10000, "1", "2", "3", "4", "5", "6", "7", "8"],
            ["NO2", 10.10, 100, 200, 300, 400, 500, 600, 700, 800],
            ["NO3", False, 100, 200, 300, 400, 500, 600, 700, 800],
        ],
        columns=[
            "ConsumerID",
            "PowerNode",
            "ReservePrice",  # 1
            "PriceElasticity",  # 2
            "MinPriceLimit",  # 3
            "MaxPriceLimit",  # 4
            "NormalPrice",  # 5
            "CapacityProfile",  # 6
            "TemperatureProfile",  # 7
            "Capacity",  # 8
        ],
    )
    with pytest.raises(SchemaErrors, match="expected series 'PowerNode' to have type str"):
        DemandSchema.validate(invalid_data, lazy=True)


def test_demand_schema_consumer_id_non_nullable() -> None:
    invalid_data = pd.DataFrame(
        [
            [None, 10000, "1", "2", "3", "4", "5", "6", "7", "8"],
        ],
        columns=[
            "ConsumerID",
            "PowerNode",
            "ReservePrice",  # 1
            "PriceElasticity",  # 2
            "MinPriceLimit",  # 3
            "MaxPriceLimit",  # 4
            "NormalPrice",  # 5
            "CapacityProfile",  # 6
            "TemperatureProfile",  # 7
            "Capacity",  # 8
        ],
    )
    with pytest.raises(SchemaError, match="non-nullable series 'ConsumerID' contains null values"):
        DemandSchema.validate(invalid_data, lazy=False)


def test_demand_schema_power_node_non_nullable() -> None:
    invalid_data = pd.DataFrame(
        [
            ["NO1", None, "1", "2", "3", "4", "5", "6", "7", "8"],
        ],
        columns=[
            "ConsumerID",
            "PowerNode",
            "ReservePrice",  # 1
            "PriceElasticity",  # 2
            "MinPriceLimit",  # 3
            "MaxPriceLimit",  # 4
            "NormalPrice",  # 5
            "CapacityProfile",  # 6
            "TemperatureProfile",  # 7
            "Capacity",  # 8
        ],
    )
    with pytest.raises(SchemaError, match="non-nullable series 'PowerNode' contains null values"):
        DemandSchema.validate(invalid_data, lazy=False)


def test_demand_schema_capacity_non_nullable() -> None:
    invalid_data = pd.DataFrame(
        [
            ["NO1", "NO1_node", "1", "2", "3", "4", "5", "6", "7", None],
        ],
        columns=[
            "ConsumerID",
            "PowerNode",
            "ReservePrice",  # 1
            "PriceElasticity",  # 2
            "MinPriceLimit",  # 3
            "MaxPriceLimit",  # 4
            "NormalPrice",  # 5
            "CapacityProfile",  # 6
            "TemperatureProfile",  # 7
            "Capacity",  # 8
        ],
    )
    with pytest.raises(SchemaError, match="non-nullable series 'Capacity' contains null values"):
        DemandSchema.validate(invalid_data, lazy=False)


@pytest.mark.parametrize(
    ("test_row", "column_to_test"),
    [
        (["NO1", "NO1_node", -1, "2", "3", "4", "5", "6", "7", "8"], "ReservePrice"),
        (["NO1", "NO1_node", "1", "2", -3, "4", "5", "6", "7", "8"], "MinPriceLimit"),
        (["NO1", "NO1_node", "1", "2", "3", -4, "5", "6", "7", "8"], "MaxPriceLimit"),
        (["NO1", "NO1_node", "1", "2", "3", "4", -5, "6", "7", "8"], "NormalPrice"),
        (["NO1", "NO1_node", "1", "2", "3", "4", "5", "6", "7", -8], "Capacity"),
    ],
)
def test_demand_schema_numeric_values_greater_than_or_equal_to_0(test_row: list, column_to_test: str) -> None:
    invalid_data = pd.DataFrame(
        data=[
            test_row,
        ],
        columns=[
            "ConsumerID",
            "PowerNode",
            "ReservePrice",  # 1
            "PriceElasticity",  # 2
            "MinPriceLimit",  # 3
            "MaxPriceLimit",  # 4
            "NormalPrice",  # 5
            "CapacityProfile",  # 6
            "TemperatureProfile",  # 7
            "Capacity",  # 8
        ],
    )
    match_message = f"Column '{column_to_test}' failed element-wise validator number 1: <Check numeric_values_greater_than_or_equal_to_0>"
    with pytest.raises(SchemaError, match=re.escape(match_message)):
        DemandSchema.validate(invalid_data)


def test_demand_schema_values_less_than_or_equal_to_zero_price_elasticity() -> None:
    invalid_data = pd.DataFrame(
        [
            ["NO1", "NO1_node", "1", 2, "3", "4", "5", "6", "7", "8"],
        ],
        columns=[
            "ConsumerID",
            "PowerNode",
            "ReservePrice",  # 1
            "PriceElasticity",  # 2
            "MinPriceLimit",  # 3
            "MaxPriceLimit",  # 4
            "NormalPrice",  # 5
            "CapacityProfile",  # 6
            "TemperatureProfile",  # 7
            "Capacity",  # 8
        ],
    )
    match_message = "Column 'PriceElasticity' failed element-wise validator number 1: <Check numeric_values_less_than_or_equal_to_0>"
    with pytest.raises(SchemaError, match=re.escape(match_message)):
        DemandSchema.validate(invalid_data)


def test_demand_schema_capacity_profile_values_are_between_or_equal_to_zero_and_one() -> None:
    invalid_data = pd.DataFrame(
        [
            ["NO1", "NO1_node", "1", "6", "3", "4", "5", 6, "7", "8"],
        ],
        columns=[
            "ConsumerID",
            "PowerNode",
            "ReservePrice",  # 1
            "PriceElasticity",  # 2
            "MinPriceLimit",  # 3
            "MaxPriceLimit",  # 4
            "NormalPrice",  # 5
            "CapacityProfile",  # 6
            "TemperatureProfile",  # 7
            "Capacity",  # 8
        ],
    )
    match_message = "Column 'CapacityProfile' failed element-wise validator number 1: <Check numeric_values_are_between_or_equal_to_0_and_1>"
    with pytest.raises(SchemaError, match=re.escape(match_message)):
        DemandSchema.validate(invalid_data)


def test_demand_meta_data_schema() -> None:
    valid_data = pd.DataFrame(
        [
            ["ConsumerID", None, None, None, "Unique consumer ID.", None, None, None, None],
            ["Capacity", "float", "Demand.Consumers.capacity", "MW", None, True, None, None, None],
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
    DemandMetadataSchema.validate(valid_data, lazy=True)


def test_demand_meta_data_schema_check_capacity_unit() -> None:
    invalid_data = pd.DataFrame(
        [
            ["ConsumerID", None, None, None, "", None, None, None, None],
            ["Capacity", "float", "Demand.Consumers.capacity", 1, "", True, None, None, None],
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

    message = "expected series 'Unit' to have type str"
    with pytest.raises(SchemaError, match=re.escape(message)):
        DemandMetadataSchema.validate(invalid_data, lazy=False)
