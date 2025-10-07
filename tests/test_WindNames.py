from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd

from framdata.database_names.WindSolarNames import WindNames


# TODO: mock _parse_args
@patch("framdata.database_names.WindSolarNames.Wind", new_callable=MagicMock)
def test_create_component(mock_wind: MagicMock):
    mock_wind_instance = MagicMock()
    mock_wind.return_value = mock_wind_instance

    WindNames._parse_args = MagicMock(
        return_value={  # the columns in columns_to_parse
            "Capacity": "DK1_wind_offshore_new_capacity",
            "Profile": "DK1_wind_offshore_new_profile",
        },
    )
    WindNames._add_meta = MagicMock()

    row = np.array(
        [
            "DK1_wind_offshore_new",
            "DK1_wind_offshore_new_capacity",
            "DK1_wind_offshore_new_node",
            "DK1_wind_offshore_new_profile",  # alt dette er en rad i filen
            "Wind_Offshore",
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

    result = WindNames.create_component(row, indices, meta_columns, meta_data)
    expected = {
        "DK1_wind_offshore_new": mock_wind_instance,
    }  # ID for the power plant, same as the first value of the row above

    assert result == expected
    # test that the Wind object in instantiated with the correct arguments
    mock_wind.assert_called_once()

    WindNames._add_meta.assert_called_once_with(
        mock_wind_instance, row, indices, meta_columns,
    )
