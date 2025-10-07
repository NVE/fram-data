import re
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest
from framcore.timeindexes import FixedFrequencyTimeIndex

from framdata.loaders import NVEExcelTimeVectorLoader

EXPECTED_VECTOR = "expected_vector"
DATETIME_INDEX = "DateTime"
TEST_FILENAME = "test_time_vectors.xlsx"


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
        "Currency": None,
    }


@pytest.fixture
def test_time_vector() -> pd.DataFrame:
    tv_df = pd.DataFrame()
    tv_df[EXPECTED_VECTOR] = [1.0, 2.0, 3.0, 4.0, 5.0]
    tv_df["wrong_vector"] = [0.0, 0.0, 0.0, 0.0, 0.0]
    tv_df[DATETIME_INDEX] = pd.date_range(start="2025-03-14 00:00:00", periods=5, freq="h")

    return tv_df


@pytest.fixture
def test_time_vector_horizontal_format() -> pd.DataFrame:
    simple_columns = ["ID", 2025, 2026, 2030, 2040, 2045]
    expected_vector_row = [EXPECTED_VECTOR, 1.0, 2.0, 3.0, 4.0, 5.0]
    wrong_vector_row = ["wrong_vector", 0.0, 0.0, 0.0, 0.0, 0.0]

    return pd.DataFrame.from_dict(
        data={0: expected_vector_row, 1: wrong_vector_row},
        orient="index",
        columns=simple_columns,
    )


# ----- GET VALUES ----- #
def test_get_values(tmp_path: Path, test_time_vector: pd.DataFrame):
    test_excel = tmp_path / TEST_FILENAME
    test_time_vector.to_excel(test_excel, sheet_name="Data", index=False)
    test_loader = NVEExcelTimeVectorLoader(source=tmp_path, relative_loc=TEST_FILENAME, validate=False, require_whole_years=False)
    test_loader._is_horizontal_format = MagicMock(return_value=False)

    expected = test_time_vector[EXPECTED_VECTOR].to_numpy()
    result = test_loader.get_values(vector_id=EXPECTED_VECTOR)
    assert np.array_equal(result, expected)
    test_loader._is_horizontal_format.assert_called_once()


def test_get_values_caches(tmp_path: Path, test_time_vector: pd.DataFrame):
    test_excel = tmp_path / TEST_FILENAME
    test_time_vector.to_excel(test_excel, sheet_name="Data", index=False)
    test_loader = NVEExcelTimeVectorLoader(source=tmp_path, relative_loc=TEST_FILENAME, validate=False, require_whole_years=False)
    test_loader._is_horizontal_format = MagicMock(return_value=False)

    __ = test_loader.get_values(vector_id=EXPECTED_VECTOR)
    assert isinstance(test_loader._data, pd.DataFrame)
    assert EXPECTED_VECTOR in test_loader._data.columns
    expected = test_time_vector[EXPECTED_VECTOR]
    result = test_loader._data[EXPECTED_VECTOR]
    pd.testing.assert_series_equal(result, expected)


def test_get_values_reads_cache(test_time_vector_horizontal_format: pd.DataFrame, test_time_vector: pd.DataFrame):
    class TestNveExcelTimeVectorLoader(NVEExcelTimeVectorLoader):
        def __init__(self):
            self._data = test_time_vector
            self._index = None

            self._meta = None

    test_loader = TestNveExcelTimeVectorLoader()
    test_loader.get_source = MagicMock(return_value="")
    test_loader._process_horizontal_format = MagicMock(return_value=test_time_vector)
    test_loader._is_horizontal_format = MagicMock(return_value=True)
    with patch("pandas.read_excel") as mock_read_excel:
        __ = test_loader.get_values(vector_id=EXPECTED_VECTOR)
        test_loader.get_source.assert_not_called()
        mock_read_excel.assert_not_called()
        test_loader._process_horizontal_format.assert_not_called()
        test_loader._process_horizontal_format.assert_not_called()


def test_get_values_horizontal_format(
    tmp_path: Path,
    test_time_vector: pd.DataFrame,
    test_time_vector_horizontal_format: pd.DataFrame,
):
    test_excel = tmp_path / TEST_FILENAME
    test_time_vector_horizontal_format.to_excel(test_excel, sheet_name="Data", index=False)
    test_loader = NVEExcelTimeVectorLoader(source=tmp_path, relative_loc=TEST_FILENAME, validate=False, require_whole_years=False)
    test_loader._is_horizontal_format = MagicMock(return_value=True)
    test_loader._process_horizontal_format = MagicMock(return_value=test_time_vector)

    expected = test_time_vector[EXPECTED_VECTOR].to_numpy()
    result = test_loader.get_values(vector_id=EXPECTED_VECTOR)
    assert np.array_equal(result, expected)
    test_loader._is_horizontal_format.assert_called_once()

    # calls format processing
    pd.testing.assert_frame_equal(
        test_time_vector_horizontal_format,
        test_loader._process_horizontal_format.call_args.args[0],
        check_dtype=False,
    )

    pd.testing.assert_frame_equal(test_time_vector, test_loader._data, check_dtype=False)  # caches


# ----- GET_INDEX ----- #
def test_get_index(test_metadata: dict, test_time_vector: pd.DataFrame):
    class TestNveExcelTimeVectorLoader(NVEExcelTimeVectorLoader):
        def __init__(self):
            self._data = test_time_vector
            self._index = None

            self._meta = None

    test_loader = TestNveExcelTimeVectorLoader()
    test_loader.get_values = MagicMock(return_value=test_time_vector[DATETIME_INDEX].to_numpy())
    test_loader.get_metadata = MagicMock(return_value=test_metadata)

    result = test_loader.get_index("")  # argument shouldnt matter in this loader
    assert isinstance(result, FixedFrequencyTimeIndex)
    assert result.get_period_duration() == timedelta(hours=1)
    assert result.get_num_periods() == 5
    assert result.get_start_time() == datetime(year=2025, month=3, day=14, hour=00, minute=00, second=00)


# ----- FORMATTING ----- #
def test_process_horizontal_format(test_time_vector: pd.DataFrame, test_time_vector_horizontal_format: pd.DataFrame):
    class TestNveExcelTimeVectorLoader(NVEExcelTimeVectorLoader):
        def __init__(self):
            self._data = None
            self._index = None
            self._meta = None

    test_loader = TestNveExcelTimeVectorLoader()
    test_loader._to_iso_datetimes = MagicMock(
        return_value=pd.date_range(start="2025-03-14 00:00:00", periods=5, freq="h"),
    )

    result = test_loader._process_horizontal_format(test_time_vector_horizontal_format)
    assert set(result.columns) == set(test_time_vector.columns)  # check column equality
    expected = test_time_vector[list(result.columns)]  # get correct order

    # names of index and dtypes becomes different here but that doesnt matter so we disable checks for those
    pd.testing.assert_frame_equal(result, expected, check_dtype=False, check_names=False)


@pytest.mark.parametrize(
    ("test_input", "expected"),
    [
        ([2025], ["2024-12-30 00:00:00"]),
        (["2025-10"], ["2025-10-01 00:00:00"]),
        (["2025-10-10"], ["2025-10-10 00:00:00"]),
        (["2025-10-10 01"], ["2025-10-10 01:00:00"]),
        (["2025-10-10 01:01"], ["2025-10-10 01:01:00"]),
        (["2025-10-10 01:01:01"], ["2025-10-10 01:01:01"]),
    ],
)
def test_to_iso_datetime(test_input, expected):
    class TestNveExcelTimeVectorLoader(NVEExcelTimeVectorLoader):
        def __init__(self):
            self._source = "test_source"
            self._relative_loc = "relative_loc"

    test_loader = TestNveExcelTimeVectorLoader()

    result = [str(v) for v in test_loader._to_iso_datetimes(pd.Series(test_input))]

    assert result == expected


def test_to_iso_datetime_raises_error():
    class TestNveExcelTimeVectorLoader(NVEExcelTimeVectorLoader):
        def __init__(self):
            self._source = "test_source"
            self._relative_loc = "relative_loc"

    test_loader = TestNveExcelTimeVectorLoader()
    test_input = "invalid_value"
    msg = f"Loader {test_loader} could not convert value '{test_input}' to datetime format. Check formatting, for example number of spaces."
    with pytest.raises(RuntimeError, match=re.escape(msg)):
        test_loader._to_iso_datetimes(pd.Series([test_input]))
