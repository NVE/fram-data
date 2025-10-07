from unittest.mock import MagicMock, patch

import numpy as np

from framdata.database_names.nodes_names import NodesNames


@patch("framdata.database_names.nodes_names.Node", new_callable=MagicMock)
def test_create_component(mock_node: MagicMock):
    NodesNames._parse_args = MagicMock(return_value={"ExogenPrice": "300 EUR/MWh", "PriceProfile": "NO1_Profile"})
    NodesNames._add_meta = MagicMock()

    mock_node_instance = MagicMock()
    mock_node.return_value = mock_node_instance

    row = np.array(["NO1", None, "electricity", 300, "NO1_Profile", False, "membership"], dtype=object)
    indices = {
        "NodeID": 0,
        "NiceName": 1,
        "Commodity": 2,
        "ExogenPrice": 3,
        "PriceProfile": 4,
        "IsExogenous": 5,
        "MemberColumn": 6,
    }
    meta_columns = {"MemberColumns"}
    meta_data = "testmeta"

    expected = {"NO1": mock_node_instance}

    result = NodesNames.create_component(row, indices, meta_columns, meta_data)
    assert result == expected
    mock_node.assert_called_once()
    NodesNames._parse_args.assert_called_once_with(row, indices, ["ExogenPrice", "PriceProfile"], meta_data)
    NodesNames._add_meta.assert_called_once_with(mock_node_instance, row, indices, meta_columns)
