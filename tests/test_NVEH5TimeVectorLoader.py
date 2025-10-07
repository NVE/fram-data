import re
from collections import defaultdict
from pathlib import Path
from unittest.mock import patch

import h5py
import numpy as np
import pandas as pd
import pytest
from framcore.timeindexes import FixedFrequencyTimeIndex, ListTimeIndex

from framdata.loaders import NVEH5TimeVectorLoader

EXPECTED_VECTOR = "expected_vector"
DATETIME_INDEX = "DateTime"
TEST_FILENAME = "test_time_vectors.h5"


def create_tmp_file(file_path: Path):
    with file_path.open("w") as f:
        f.write("")


class TestH5Loader(NVEH5TimeVectorLoader):
    def __init__(self, source, relative_loc=None, validate=False) -> None:
        super().__init__(source, False, relative_loc, validate=validate)

    def __repr__(self) -> str:
        """Overwrite repr to not include paths, since it interferese with matching exception messages."""
        return "TestH5Loader"


@pytest.fixture
def test_metadata() -> dict:
    return {
        "IsMaxLevel": True,
        "IsZeroOneProfile": False,
        "Is52WeekYears": False,
        "ExtrapolateFirstPoint": False,
        "ExtrapolateLastPoint": False,
        "Isrotating": False,
        "IsMeanOne": False,
        "StartYear": 2025,
        "NumYears": 1,
        "StartDateTime": pd.to_datetime("2025-03-14 00:00:00"),
        "Frequency": pd.to_timedelta("1h"),  # hour
        "NumberOfPoints": 5,
        "TimeZone": None,
        "Unit": None,
        "RefPeriodNumberOfYears": None,
        "RefPeriodStartYear": None,
    }


@pytest.fixture
def test_data(test_metadata: dict) -> pd.DataFrame:
    tv_dict = defaultdict(dict)
    tv_dict["vectors"][EXPECTED_VECTOR] = np.array([1, 2, 3, 4, 5])
    tv_dict["vectors"]["wrong_vector"] = np.array([0, 0, 0, 0, 0])
    tv_dict["common_index"] = np.char.encode(pd.date_range(start="2025-03-14 00:00:00", periods=5, freq="h").astype("S").to_numpy(dtype=str), encoding="utf-8")
    tv_dict["common_metadata"] = test_metadata

    return tv_dict


def dict_to_h5_format(h5_object: h5py.File | h5py.Group, data: dict):
    for k, v in data.items():
        if isinstance(v, dict):
            dict_to_h5_format(h5_object.create_group(k), v)
        elif isinstance(v, np.ndarray):
            h5_object.create_dataset(k, data=v)
        else:
            h5_object.create_dataset(k, data=str(v).encode(encoding="utf-8"))


def write_to_h5(path: Path, data: dict) -> None:
    with h5py.File(path, mode="w") as f:
        dict_to_h5_format(f, data)


def test_read_vector(tmp_path: Path, test_data: dict) -> None:
    h5_path = tmp_path / TEST_FILENAME
    write_to_h5(h5_path, test_data)
    loader = NVEH5TimeVectorLoader(source=h5_path, require_whole_years=False, validate=False)
    with h5py.File(h5_path, mode="r") as f:
        result = loader._read_vector_field(f, "vectors", EXPECTED_VECTOR, h5py.Dataset, use_fallback=False)[()]

    assert np.array_equal(result, test_data["vectors"][EXPECTED_VECTOR])


def test_read_common_index(tmp_path: Path, test_data: dict) -> None:
    h5_path = tmp_path / TEST_FILENAME
    write_to_h5(h5_path, test_data)
    loader = NVEH5TimeVectorLoader(source=h5_path, require_whole_years=False, validate=False)
    with h5py.File(h5_path, mode="r") as f:
        result = loader._read_vector_field(f, "index", EXPECTED_VECTOR, h5py.Dataset, use_fallback=True)[()]

    assert np.array_equal(result, test_data["common_index"])


def test_read_common_metadata(tmp_path: Path, test_data: dict) -> None:
    h5_path = tmp_path / TEST_FILENAME
    write_to_h5(h5_path, test_data)
    loader = NVEH5TimeVectorLoader(source=h5_path, require_whole_years=False, validate=False)
    with h5py.File(h5_path, mode="r") as f:
        result = loader._read_vector_field(f, "metadata", EXPECTED_VECTOR, h5py.Group, use_fallback=True)
        result = {k: v[()] for k, v in result.items()}
    assert result == {k: str(v).encode(encoding="utf-8") for k, v in test_data["common_metadata"].items()}


def test_read_non_existant_vector(tmp_path: Path, test_data: dict) -> None:
    h5_path = tmp_path / TEST_FILENAME
    write_to_h5(h5_path, test_data)
    loader = TestH5Loader(source=h5_path)
    expected_message = f"{loader} expected 'v1' in {h5py.Group} 'vectors' but 'v1' was not found in 'vectors' group."
    with h5py.File(h5_path, mode="r") as f, pytest.raises(KeyError, match=re.escape(expected_message)):
        result = loader._read_vector_field(f, "vectors", "v1", h5py.Dataset, use_fallback=False)[()]


def test_read_non_existant_field(tmp_path: Path, test_data: dict) -> None:
    h5_path = tmp_path / TEST_FILENAME
    write_to_h5(h5_path, test_data)

    loader = TestH5Loader(source=h5_path)

    field_name = "field"
    vector_name = "v1"
    expected_message = f"{loader} expected '{vector_name}' in {h5py.Group} '{field_name}' but '{field_name}' was not found in file."
    with h5py.File(h5_path, mode="r") as f, pytest.raises(KeyError, match=re.escape(expected_message)):
        result = loader._read_vector_field(f, field_name, vector_name, h5py.Dataset, use_fallback=False)[()]


def test_read_non_existant_field_or_fallback(tmp_path: Path, test_data: dict) -> None:
    h5_path = tmp_path / TEST_FILENAME
    write_to_h5(h5_path, test_data)

    loader = TestH5Loader(source=h5_path)

    field_name = "field"
    vector_name = "v1"
    expected_message = (
        f"{loader} expected '{vector_name}' in {h5py.Group} '{field_name}' "
        f"or a fallback {h5py.Dataset} 'common_{field_name}' in H5 file but "
        f"'{field_name}' was not found in file,"
        f" and fallback {h5py.Dataset} 'common_{field_name}' not found in file."
    )
    with h5py.File(h5_path, mode="r") as f, pytest.raises(KeyError, match=re.escape(expected_message)):
        result = loader._read_vector_field(f, field_name, vector_name, h5py.Dataset, use_fallback=True)[()]
