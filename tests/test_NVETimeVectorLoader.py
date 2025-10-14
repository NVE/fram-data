from datetime import datetime, timedelta

from framcore.timeindexes import ConstantTimeIndex, FixedFrequencyTimeIndex, ListTimeIndex, SinglePeriodTimeIndex

from framdata.loaders import NVETimeVectorLoader


def test_create_index_fixed_frequency():
    class TestNVETimeVectorLoader(NVETimeVectorLoader):
        def __init__(self):
            pass

    TestNVETimeVectorLoader.__abstractmethods__ = None

    test_loader = TestNVETimeVectorLoader()

    datetimes = [
        datetime.fromisocalendar(2025, 1, 1),
        datetime.fromisocalendar(2025, 1, 2),
        datetime.fromisocalendar(2025, 1, 3),
        datetime.fromisocalendar(2025, 1, 4),
    ]
    result = test_loader._create_index(datetimes, False, False, False)

    assert isinstance(result, FixedFrequencyTimeIndex)
    assert result.get_num_periods() == len(datetimes)
    assert result.get_period_duration() == timedelta(days=1)
    assert result.get_start_time() == datetime.fromisocalendar(2025, 1, 1)


def test_create_index_list_index():
    class TestNVETimeVectorLoader(NVETimeVectorLoader):
        def __init__(self):
            pass

    TestNVETimeVectorLoader.__abstractmethods__ = None

    test_loader = TestNVETimeVectorLoader()

    datetimes = [
        datetime.fromisocalendar(2025, 1, 1),
        datetime.fromisocalendar(2025, 1, 2),
        datetime.fromisocalendar(2025, 1, 3),
        datetime.fromisocalendar(2025, 1, 5),
    ]
    result = test_loader._create_index(datetimes, False, False, False)

    assert isinstance(result, ListTimeIndex)
    assert result.get_num_periods() == len(datetimes)
    assert result.get_datetime_list() == [*datetimes, datetime.fromisocalendar(2026, 1, 1)]


def test_create_index_yearly_list():
    class TestNVETimeVectorLoader(NVETimeVectorLoader):
        def __init__(self):
            pass

    TestNVETimeVectorLoader.__abstractmethods__ = None

    test_loader = TestNVETimeVectorLoader()

    datetimes = [
        datetime.fromisocalendar(2025, 1, 1),
        datetime.fromisocalendar(2026, 1, 1),
        datetime.fromisocalendar(2028, 1, 1),
        datetime.fromisocalendar(2029, 1, 1),
    ]
    result = test_loader._create_index(datetimes, False, False, False)

    assert isinstance(result, ListTimeIndex)
    assert result.get_num_periods() == len(datetimes)
    assert result.get_datetime_list() == [*datetimes, datetime.fromisocalendar(2030, 1, 1)]


def test_create_index_single_period():
    class TestNVETimeVectorLoader(NVETimeVectorLoader):
        def __init__(self):
            pass

    TestNVETimeVectorLoader.__abstractmethods__ = None

    test_loader = TestNVETimeVectorLoader()

    datetimes = [
        datetime.fromisocalendar(2025, 1, 1),
    ]
    result = test_loader._create_index(datetimes, False, False, False)

    assert isinstance(result, SinglePeriodTimeIndex)
    assert result.get_num_periods() == len(datetimes)
    assert result.get_period_duration() == timedelta(days=364)
    assert result.get_start_time() == datetime.fromisocalendar(2025, 1, 1)


def test_create_index_constant():
    class TestNVETimeVectorLoader(NVETimeVectorLoader):
        def __init__(self):
            pass

    TestNVETimeVectorLoader.__abstractmethods__ = None

    test_loader = TestNVETimeVectorLoader()

    datetimes = [
        datetime.fromisocalendar(2025, 1, 1),
    ]
    result = test_loader._create_index(datetimes, False, True, True)

    assert isinstance(result, ConstantTimeIndex)
