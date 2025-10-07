from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd

from framdata.database_names.ThermalNames import ThermalNames


@patch("framdata.database_names.ThermalNames.Thermal", new_callable=MagicMock)
@patch("framdata.database_names.ThermalNames.StartUpCost", new_callable=MagicMock)
def test_create_component(mock_startupcost: MagicMock, mock_thermal: MagicMock):
    mock_startupcost_instance = MagicMock()
    mock_startupcost.return_value = mock_startupcost_instance
    mock_thermal_instance = MagicMock()
    mock_thermal.return_value = mock_thermal_instance

    ThermalNames._parse_args = MagicMock(
        return_value={
            "EmissionNode": "CO2",
            "Capacity": "100 MW",
            "FullLoadEfficiency": "0.5",
            "PartLoadEfficiency": "0.3",
            "VOC": "1 EUR/MWh",
            "StartCosts": "10 EUR/MW",
            "StartHours": "2",
            "MinStableLoad": "0.1",
            "MinOperationalBound": "NO1_Gas_min",
            "MaxOperationalBound": "NO1_Gas_max",
            "EmissionCoefficient": "0.2 t/MWh",
        },
    )
    ThermalNames._add_meta = MagicMock()

    row = np.array(
        [
            "NO1_Gas",
            "NO1_Gas_node",
            "Gas",
            "CO2",
            100,
            0.5,
            0.3,
            1,
            10,
            2,
            0.1,
            "NO1_Gas_min",
            "NO1_Gas_max",
            0.2,
            "membership",
        ],
        dtype=object,
    )
    indices = {
        "ThermalID": 0,
        "PowerNode": 1,
        "FuelNode": 2,
        "EmissionNode": 3,
        "Capacity": 4,
        "FullLoadEfficiency": 5,
        "PartLoadEfficiency": 6,
        "VOC": 7,
        "StartCosts": 8,
        "StartHours": 9,
        "MinStableLoad": 10,
        "MinOperationalBound": 11,
        "MaxOperationalBound": 12,
        "EmissionCoefficient": 13,
        "MemberColumn": 14,
    }
    meta_columns = {"MemberColumn"}

    meta_data = pd.DataFrame(
        [
            ["FullLoadEfficiency", None],
            ["PartLoadEfficiency", None],
            ["Capacity", "MW"],
            ["MaxOperationalBound", None],
            ["MinOperationalBound", None],
            ["VOC", "EUR/MWh"],
            ["StartCosts", "EUR/MW"],
            ["StartHours", None],
            ["MinStableLoad", None],
            ["EmissionCoefficient", "t/MWh"],
        ],
        columns=["attribute", "unit"],
    )

    result = ThermalNames.create_component(row, indices, meta_columns, meta_data)
    expected = {"NO1_Gas": mock_thermal_instance}

    assert result == expected
    mock_thermal.assert_called_once()
    mock_startupcost.assert_called_once()
    ThermalNames._add_meta.assert_called_once_with(mock_thermal_instance, row, indices, meta_columns)
