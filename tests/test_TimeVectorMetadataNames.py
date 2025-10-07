import pytest

from framdata.database_names.TimeVectorMetadataNames import TimeVectorMetadataNames as TvMn


@pytest.fixture
def test_meta() -> dict:
    return {
        TvMn.ID_COLUMN_NAME: True,
        TvMn.IS_MAX_LEVEL: None,
        TvMn.IS_ZERO_ONE_PROFILE: b"False",
        TvMn.REF_PERIOD_START_YEAR: "0",
        TvMn.REF_PERIOD_NUM_YEARS: 10,
        # TvMn.START: pd.to_datetime,
        # TvMn.FREQUENCY: pd.to_timedelta,
        TvMn.NUM_POINTS: b"None",
        # TvMn.TIMEZONE: pytz.timezone,
        TvMn.UNIT: "str",
        TvMn.CURRENCY: "str",
        TvMn.IS_52_WEEK_YEARS: b"False",
        TvMn.EXTRAPOLATE_FISRT_POINT: True,
        TvMn.EXTRAPOLATE_LAST_POINT: False,
    }


def test_cast_meta(test_meta: dict):
    result_meta, result_missing = TvMn.cast_meta(test_meta)

    expected_meta = {
        TvMn.ID_COLUMN_NAME: "True",
        TvMn.IS_MAX_LEVEL: None,
        TvMn.IS_ZERO_ONE_PROFILE: False,
        TvMn.REF_PERIOD_START_YEAR: 0,
        TvMn.REF_PERIOD_NUM_YEARS: 10,
        # TvMn.START: pd.to_datetime,
        # TvMn.FREQUENCY: pd.to_timedelta,
        TvMn.NUM_POINTS: None,
        # TvMn.TIMEZONE: pytz.timezone,
        TvMn.UNIT: "str",
        TvMn.CURRENCY: "str",
        TvMn.IS_52_WEEK_YEARS: False,
        TvMn.EXTRAPOLATE_FISRT_POINT: True,
        TvMn.EXTRAPOLATE_LAST_POINT: False,
    }

    expected_missing = {TvMn.START, TvMn.FREQUENCY, TvMn.TIMEZONE}

    assert result_meta == expected_meta
    assert result_missing == expected_missing
