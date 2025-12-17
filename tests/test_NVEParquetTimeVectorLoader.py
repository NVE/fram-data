from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest
from framcore.timeindexes import FixedFrequencyTimeIndex, ListTimeIndex

from framdata.loaders import NVEParquetTimeVectorLoader

EXPECTED_VECTOR = "expected_vector"
DATETIME_INDEX = "DateTime"
TEST_FILENAME = "test_time_vectors.parquet"


def create_tmp_file(file_path: Path):
    with file_path.open("w") as f:
        f.write("")


@pytest.fixture
def test_metadata() -> dict:
    return {
        "IsMaxLevel": True,
        "ISZeroOneProfile": True,
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
    }


@pytest.fixture
def test_time_vector() -> pd.DataFrame:
    tv_df = pd.DataFrame()
    tv_df[EXPECTED_VECTOR] = [1, 2, 3, 4, 5]
    tv_df["wrong_vector"] = [0, 0, 0, 0, 0]
    tv_df[DATETIME_INDEX] = pd.date_range(start="2025-03-14 00:00:00", periods=5, freq="h")

    return tv_df


# ----- GET VALUES ----- #
def test_get_values(tmp_path: Path, test_time_vector: pd.DataFrame):
    test_parquet = tmp_path / TEST_FILENAME
    test_time_vector.to_parquet(test_parquet)
    test_loader = NVEParquetTimeVectorLoader(source=tmp_path, relative_loc=TEST_FILENAME, require_whole_years=False, validate=False)
    expected = test_time_vector[EXPECTED_VECTOR].to_numpy()
    result = test_loader.get_values(vector_id=EXPECTED_VECTOR)
    assert np.array_equal(result, expected)


def test_get_values_caches(tmp_path: Path, test_time_vector: pd.DataFrame):
    test_parquet = tmp_path / TEST_FILENAME
    test_time_vector.to_parquet(test_parquet)
    test_loader = NVEParquetTimeVectorLoader(source=tmp_path, relative_loc=TEST_FILENAME, require_whole_years=False, validate=False)
    __ = test_loader.get_values(vector_id=EXPECTED_VECTOR)

    assert isinstance(test_loader._data, dict)
    assert EXPECTED_VECTOR in test_loader._data
    expected = test_time_vector[EXPECTED_VECTOR].to_numpy()
    result = test_loader._data[EXPECTED_VECTOR]
    assert np.array_equal(result, expected)


def test_get_values_reads_cache(tmp_path: Path, test_time_vector: pd.DataFrame):
    class TestNveParquetTimeVectorLoader(NVEParquetTimeVectorLoader):
        def __init__(self):
            self._data = test_time_vector

    test_loader = TestNveParquetTimeVectorLoader()

    with patch("pandas.read_parquet") as mock_read_parquet:
        __ = test_loader.get_values(vector_id=EXPECTED_VECTOR)
        mock_read_parquet.assert_not_called()


# ----- GET_INDEX ----- #
def test_get_index_all_metadata_defined(tmp_path: Path, test_metadata: dict, test_time_vector: pd.DataFrame):
    class TestNveParquetTimeVectorLoader(NVEParquetTimeVectorLoader):
        def get_metadata(self, vector_id: str):
            return test_metadata

    test_parquet = tmp_path / TEST_FILENAME
    test_time_vector.to_parquet(test_parquet)
    test_loader = TestNveParquetTimeVectorLoader(source=tmp_path, relative_loc=TEST_FILENAME, require_whole_years=False, validate=False)
    expected = FixedFrequencyTimeIndex(
        start_time=test_metadata["StartDateTime"],
        period_duration=test_metadata["Frequency"],
        num_periods=test_metadata["NumberOfPoints"],
        is_52_week_years=test_metadata["Is52WeekYears"],
        extrapolate_first_point=test_metadata["ExtrapolateFirstPoint"],
        extrapolate_last_point=test_metadata["ExtrapolateLastPoint"],
    )
    result = test_loader.get_index("")
    assert isinstance(result, FixedFrequencyTimeIndex)
    assert result.__dict__ == expected.__dict__


def test_get_index_no_frequency(tmp_path: Path, test_metadata: dict, test_time_vector: pd.DataFrame):
    test_metadata["Frequency"] = None

    class TestNveParquetTimeVectorLoader(NVEParquetTimeVectorLoader):
        def get_metadata(self, vector_id: str):
            return test_metadata

    test_parquet = tmp_path / TEST_FILENAME
    test_time_vector.to_parquet(test_parquet)
    test_loader = TestNveParquetTimeVectorLoader(source=tmp_path, relative_loc=TEST_FILENAME, require_whole_years=False, validate=False)

    result = test_loader.get_index("")
    assert isinstance(result, FixedFrequencyTimeIndex)
    assert result.get_period_duration() == timedelta(hours=1)
    assert result.get_num_periods() == 5
    assert result.get_start_time() == datetime(year=2025, month=3, day=14, hour=00, minute=00, second=00)


def test_get_index_no_start(tmp_path: Path, test_metadata: dict, test_time_vector: pd.DataFrame):
    true_start = test_metadata["StartDateTime"]
    test_metadata["StartDateTime"] = None

    class TestNveParquetTimeVectorLoader(NVEParquetTimeVectorLoader):
        def get_metadata(self, vector_id: str):
            return test_metadata

    test_parquet = tmp_path / TEST_FILENAME
    test_time_vector.to_parquet(test_parquet)
    test_loader = TestNveParquetTimeVectorLoader(source=tmp_path, relative_loc=TEST_FILENAME, require_whole_years=False, validate=False)
    expected = FixedFrequencyTimeIndex(
        start_time=true_start,
        period_duration=test_metadata["Frequency"],
        num_periods=test_metadata["NumberOfPoints"],
        is_52_week_years=test_metadata["Is52WeekYears"],
        extrapolate_first_point=test_metadata["ExtrapolateFirstPoint"],
        extrapolate_last_point=test_metadata["ExtrapolateLastPoint"],
    )
    result = test_loader.get_index("")
    assert isinstance(result, FixedFrequencyTimeIndex)
    assert result.__dict__ == expected.__dict__


def test_get_index_no_num_points(tmp_path: Path, test_metadata: dict, test_time_vector: pd.DataFrame):
    true_num_points = test_metadata["NumberOfPoints"]
    test_metadata["NumberOfPoints"] = None

    class TestNveParquetTimeVectorLoader(NVEParquetTimeVectorLoader):
        def get_metadata(self, vector_id: str):
            return test_metadata

    test_parquet = tmp_path / TEST_FILENAME
    test_time_vector.to_parquet(test_parquet)
    test_loader = TestNveParquetTimeVectorLoader(source=tmp_path, relative_loc=TEST_FILENAME, require_whole_years=False, validate=False)
    expected = FixedFrequencyTimeIndex(
        start_time=test_metadata["StartDateTime"],
        period_duration=test_metadata["Frequency"],
        num_periods=true_num_points,
        is_52_week_years=test_metadata["Is52WeekYears"],
        extrapolate_first_point=test_metadata["ExtrapolateFirstPoint"],
        extrapolate_last_point=test_metadata["ExtrapolateLastPoint"],
    )
    result = test_loader.get_index("")
    assert isinstance(result, FixedFrequencyTimeIndex)
    assert result.__dict__ == expected.__dict__
