from pathlib import Path
from typing import ClassVar
from unittest.mock import MagicMock, Mock, call

import pandas as pd
import pytest

from framdata.populators.NVEEnergyModelPopulator import NVEEnergyModelPopulator
from framdata.populators.NVEPathManager import NVEPathManager

TEST_SOURCE = Path("source")
TEST_RELATIVE_LOC = Path("relative_loc")


def create_tmp_file(file_path: Path):
    with file_path.open("w") as f:
        f.write("")


@pytest.fixture
def dbn_path():
    return "framdata.NVEEnergyModelPopulator.DbN"


@pytest.mark.parametrize(
    ("test_input", "expected"),
    [(NVEPathManager(TEST_SOURCE, [], []), TEST_SOURCE), (TEST_SOURCE, TEST_SOURCE), ("source", TEST_SOURCE)],
)
def test_set_source(test_input, expected) -> None:
    class TestNVEEnergyModelPopulator(NVEEnergyModelPopulator):
        def __init__(self):
            self._source = None

    populator = TestNVEEnergyModelPopulator()
    populator._check_type = Mock()

    result = populator._set_source(test_input)

    populator._check_type.assert_called_once_with(test_input, (NVEPathManager, Path, str))
    assert result == expected


def test_populate_time_vectors(tmp_path: Path) -> None:
    time_vector_id = "tv1"
    tmp_file = "test.txt"
    time_vectors = {time_vector_id: tmp_path / tmp_file}

    create_tmp_file(tmp_path / tmp_file)

    mocked_database_interpreter = MagicMock()
    mocked_get_source_and_relative_loc = Mock(return_value=(tmp_path, tmp_file))
    mocked_database_interpreter.get_source_and_relative_loc = mocked_get_source_and_relative_loc
    mocked_data_object_manager = MagicMock()
    mocked_create_time_vectors = Mock(return_value=time_vectors)
    mocked_data_object_manager.create_time_vectors = mocked_create_time_vectors

    class TestNVEEnergyModelPopulator(NVEEnergyModelPopulator):
        _TIME_VECTOR_LIST: ClassVar[list[str]] = [(time_vector_id, False)]

        def __init__(self):
            self.database_interpreter = mocked_database_interpreter
            self.data_object_manager = mocked_data_object_manager
            self._data = {}

    populator = TestNVEEnergyModelPopulator()
    populator._register_id = Mock()
    populator._populate_time_vectors()
    result = populator._data

    populator._register_id.assert_called_once()
    mocked_get_source_and_relative_loc.assert_called_once()
    mocked_create_time_vectors.assert_called_once_with(
        tmp_path,
        tmp_file,
        False,
    )

    expected = time_vectors
    assert result == expected


def test_populate_components() -> None:
    component_df = pd.DataFrame()
    meta_data = pd.DataFrame()
    mocked_db_interpreter = MagicMock()
    mocked_get_source_and_relative_loc = Mock(return_value=(TEST_SOURCE, TEST_RELATIVE_LOC))
    mocked_db_interpreter.get_source_and_relative_loc = mocked_get_source_and_relative_loc
    mocked_read_attribute_table = Mock(return_value=(component_df, meta_data))
    mocked_db_interpreter.read_attribute_table = mocked_read_attribute_table

    components = [({"component1": "data1"}, {"ref1", "ref2"}), ({"component2": "data2"}, {"ref3"})]

    class TestComponentNames:
        def create_component(self):
            pass

    class TestNVEEnergyModelPopulator(NVEEnergyModelPopulator):
        _COMPONENT_DICT: ClassVar[dict] = {"component_file_name": TestComponentNames}

        def __init__(self):
            self.database_interpreter = mocked_db_interpreter
            self._data = {}

            self._validate = False

    populator = TestNVEEnergyModelPopulator()
    populator._get_components = Mock(return_value=components)
    populator._register_id = Mock()
    populator._register_references = Mock()
    populator._register_id = Mock()
    result = populator._populate_topology_objects(populator._COMPONENT_DICT, "TEST")
    expected = {
        "component1": "data1",
        "component2": "data2",
    }

    assert result == expected
    mocked_get_source_and_relative_loc.assert_called_once()  # noqa: SLF001
    mocked_read_attribute_table.assert_called_once()  # noqa: SLF001
    populator._get_components.assert_called_once()  # noqa: SLF001
    populator._register_id.assert_has_calls([call("component1", TEST_RELATIVE_LOC), call("component2", TEST_RELATIVE_LOC)])
    populator._register_references.assert_has_calls([call("component1", {"ref1", "ref2"}), call("component2", {"ref3"})])


def test_get_components() -> None:
    test_data = pd.DataFrame(
        [
            ["DK1_Gas_1", "DK1_Gas_1_node", "Gas", 1],
            ["DK1_Gas_2", "DK1_Gas_2_node", "Gas", 2],
        ],
        columns=["ThermalID", "PowerNodeID", "FuelNodeID", "VOC"],
    )

    class TestThermalNames:
        id_col = "ThermalID"
        power_node_col = "PowerNodeID"
        fuel_node_col = "FuelNodeID"
        voc_col = "VOC"

        columns: ClassVar[list] = [id_col, power_node_col, fuel_node_col, voc_col]
        ref_columns: ClassVar[list] = [power_node_col, fuel_node_col]

        def create_component(self, row, indices, meta_columns, meta_data, attribute_objects) -> list:
            thermal_id = row[indices[TestThermalNames.id_col]]
            power_node = row[indices[TestThermalNames.power_node_col]]
            fuel_node = row[indices[TestThermalNames.fuel_node_col]]
            voc_level = row[indices[TestThermalNames.voc_col]]
            attribute_list = [thermal_id, power_node, fuel_node, voc_level]
            voc = meta_data[meta_data["attribute"] == "VOC"]
            voc_unit = voc.iloc[0]["unit"]
            attribute_list.append(voc_unit)
            return attribute_list

        def get_references(self, row, indices, ref_columns) -> set:
            return {row[indices[c]] for c in ref_columns}

    component_names = TestThermalNames()

    meta_data = pd.DataFrame(
        [
            ["ThermalID", "string", None, None, "some text"],
            ["PowerNodeId", "string", "Power.Nodes", None, "some text"],
            ["FuelNodeId", "string", "Fuel.Nodes", None, "some text"],
            ["VOC", "float", None, "EUR/MWh", "some text"],
        ],
        columns=["attribute", "dtype", "reference", "unit", "description"],
    )

    populator = NVEEnergyModelPopulator("", validate=False)
    result = populator._get_components(test_data, component_names, meta_data)
    expected = [
        (["DK1_Gas_1", "DK1_Gas_1_node", "Gas", 1, "EUR/MWh"], {"DK1_Gas_1_node", "Gas"}),
        (["DK1_Gas_2", "DK1_Gas_2_node", "Gas", 2, "EUR/MWh"], {"DK1_Gas_2_node", "Gas"}),
    ]

    assert result == expected


def test_validate_component_data():
    expected_error_data = pd.DataFrame(["error"], columns=["error"])

    class TestComponentNames:
        @classmethod
        def get_attribute_data_schema(cls) -> str:
            return "AttributeSchema"

        @classmethod
        def get_metadata_schema(cls) -> str:
            return "MetadataSchema"

        @classmethod
        def validate(cls, schema: str, data: pd.DataFrame) -> None:
            if data.empty:
                return None
            return expected_error_data

    invalid_data = pd.DataFrame(["invalid_data"], columns=["invalid_data"])

    result = NVEEnergyModelPopulator._validate_component_data(TestComponentNames, invalid_data, invalid_data)

    pd.testing.assert_frame_equal(result["attribute data"], expected_error_data)
    pd.testing.assert_frame_equal(result["metadata"], expected_error_data)
