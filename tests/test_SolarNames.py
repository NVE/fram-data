from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd

from framdata.database_names.WindSolarNames import SolarNames


# TODO: mock _parse_args
@patch("framdata.database_names.WindSolarNames.Solar", new_callable=MagicMock)
def test_create_component(mock_solar: MagicMock):
    mock_solar_instance = MagicMock()
    mock_solar.return_value = mock_solar_instance

    SolarNames._parse_args = MagicMock(
        return_value={  # the columns in columns_to_parse
            "Capacity": "Solar_DANM-DK1_capacity",
            "Profile": "DK1_solar_stock_profile",
        },
    )
    SolarNames._add_meta = MagicMock()

    row = np.array(
        [
            "Solar_DANM-DK1",
            "Solar_DANM-DK1_capacity",
            "Solar_DANM-DK1_node",
            "DK1_solar_stock_profile",  # choose values on a random row in the file
            "Solar",
        ],
        dtype=object,
    )
    # the columns for the row above (mapping columns to array)
    indices = {
        "ID": 0,
        "Capacity": 1,
        "PowerNode": 2,
        "Profile": 3,
        "TechnologyType": 4,
    }
    meta_columns = {"TechnologyType"}

    # the metadata used
    meta_data = pd.DataFrame(
        [
            ["Capacity", "MW"],
            ["Profile", None],
        ],
        columns=["attribute", "unit"],
    )

    result = SolarNames.create_component(row, indices, meta_columns, meta_data)
    expected = {
        "Solar_DANM-DK1": mock_solar_instance,
    }  # ID for the power plant, same as the first value of the row above

    assert result == expected
    # test that the Solar object in instantiated with the correct arguments
    mock_solar.assert_called_once()

    SolarNames._add_meta.assert_called_once_with(mock_solar_instance, row, indices, meta_columns)
