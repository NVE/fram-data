"""Contains names of fields in time vector metadata."""

from collections.abc import Callable
from datetime import datetime, timedelta, tzinfo
from typing import ClassVar

import pandas as pd
import pytz


class TimeVectorMetadataNames:
    """
    Denote available fields in time vector metadata, and provide functionality for time vector metadata processing.

    The processing is concerned with casting the metadata fields to correct types and decoding the fields and/or values if they are stored as bytes.

    """

    ENCODING = "utf-8"

    DATETIME_COL = "DateTime"
    # OBS! when adding new metadata entries, you also have to parse them in FileHandler.get_parquet_metadata
    # otherwise they will not be read.
    # Metadata fields

    # Id column name
    ID_COLUMN_NAME = "ID"

    # Required bools
    IS_MAX_LEVEL = "IsMaxLevel"
    IS_ZERO_ONE_PROFILE = "IsZeroOneProfile"
    IS_52_WEEK_YEARS = "Is52WeekYears"
    EXTRAPOLATE_FISRT_POINT = "ExtrapolateFirstPoint"
    EXTRAPOLATE_LAST_POINT = "ExtrapolateLastPoint"

    # reference period
    REF_PERIOD_START_YEAR = "RefPeriodStartYear"
    REF_PERIOD_NUM_YEARS = "RefPeriodNumberOfYears"

    START = "StartDateTime"
    FREQUENCY = "Frequency"
    NUM_POINTS = "NumberOfPoints"
    TIMEZONE = "TimeZone"

    UNIT = "Unit"

    METADATA_TYPES = bool | int | str | datetime | timedelta | tzinfo | None
    METADATA_TYPES_TUPLE = (bool, int, str, datetime, timedelta, tzinfo, type(None))

    # reference_period = "ReferencePeriod"

    B_IS_MAX_LEVEL = IS_MAX_LEVEL.encode(ENCODING)
    B_IS_ZERO_ONE_PROFILE = IS_ZERO_ONE_PROFILE.encode(ENCODING)
    B_IS_52_WEEK_YEARS = IS_52_WEEK_YEARS.encode(ENCODING)
    B_ID_COLUMN_NAME = ID_COLUMN_NAME.encode(ENCODING)
    B_EXTRAPOLATE_FISRT_POINT = EXTRAPOLATE_FISRT_POINT.encode(ENCODING)
    B_EXTRAPOLATE_LAST_POINT = EXTRAPOLATE_LAST_POINT.encode(ENCODING)

    # reference period
    B_REF_PERIOD_START_YEAR = REF_PERIOD_START_YEAR.encode(ENCODING)
    B_REF_PERIOD_NUM_YEARS = REF_PERIOD_NUM_YEARS.encode(ENCODING)

    B_START = START.encode(ENCODING)
    B_FREQUENCY = FREQUENCY.encode(ENCODING)
    B_NUM_POINTS = NUM_POINTS.encode(ENCODING)
    B_TIMEZONE = TIMEZONE.encode(ENCODING)
    B_UNIT = UNIT.encode(ENCODING)

    str_keys_to_bytes_map: ClassVar[dict[str, bytes]] = {
        ID_COLUMN_NAME: B_ID_COLUMN_NAME,
        IS_MAX_LEVEL: B_IS_MAX_LEVEL,
        IS_ZERO_ONE_PROFILE: B_IS_ZERO_ONE_PROFILE,
        IS_52_WEEK_YEARS: B_IS_52_WEEK_YEARS,
        EXTRAPOLATE_FISRT_POINT: B_EXTRAPOLATE_FISRT_POINT,
        EXTRAPOLATE_LAST_POINT: B_EXTRAPOLATE_LAST_POINT,
        REF_PERIOD_START_YEAR: B_REF_PERIOD_START_YEAR,
        REF_PERIOD_NUM_YEARS: B_REF_PERIOD_NUM_YEARS,
        START: B_START,
        FREQUENCY: B_FREQUENCY,
        NUM_POINTS: B_NUM_POINTS,
        TIMEZONE: B_TIMEZONE,
        UNIT: B_UNIT,
    }

    strict_bools_cast: ClassVar[set[str]] = {
        IS_52_WEEK_YEARS,
        EXTRAPOLATE_FISRT_POINT,
        EXTRAPOLATE_LAST_POINT,
    }
    keys_cast_methods: ClassVar[dict[str, Callable | type]] = {
        ID_COLUMN_NAME: str,
        IS_MAX_LEVEL: bool,
        IS_ZERO_ONE_PROFILE: bool,
        REF_PERIOD_START_YEAR: int,
        REF_PERIOD_NUM_YEARS: int,
        START: pd.to_datetime,
        FREQUENCY: pd.to_timedelta,
        NUM_POINTS: int,
        TIMEZONE: pytz.timezone,
        UNIT: str,
    }

    @staticmethod
    def cast_meta(
        raw_meta: dict[str | bytes, str | bytes | int | bool | None],
    ) -> tuple[dict[str, str, bool | int | str | datetime | timedelta | tzinfo | None], set[str]]:
        """
        Decode possible binary keys and values and cast values of metadata dict to their defined types.

        Args:
            raw_meta (dict[str  |  bytes, str  |  bytes  |  int  |  bool  |  None]): Dictionary to decode and cast.

        Returns:
            tuple[dict[str, Any], set[str]]: Decoded and cast dictionary, set of missing keys.

        """
        tvmn = TimeVectorMetadataNames
        str_bytes_map = tvmn.str_keys_to_bytes_map
        cast_meta = {key: raw_meta[key] for key in set(str_bytes_map.keys()) | set(str_bytes_map.values()) if key in raw_meta}
        str_to_bytes_meta = tvmn.bytes_keys_to_str(cast_meta)
        cast_meta = str_to_bytes_meta if str_to_bytes_meta else cast_meta  # Keys were bytes and we decode to str.

        missing_keys: set[str] = {key for key in str_bytes_map if key not in cast_meta}

        # Update with cast values for strict bools and others.
        cast_meta.update({key: tvmn.cast_strict_bool_value(cast_meta[key]) for key in tvmn.strict_bools_cast if key in cast_meta})
        cast_meta.update({key: tvmn.cast_value(cast_meta[key], cast_method) for key, cast_method in tvmn.keys_cast_methods.items() if key in cast_meta})

        return cast_meta, missing_keys

    @staticmethod
    def str_keys_to_bytes(raw_meta: dict[str, bytes]) -> dict[bytes, bytes]:
        return {bytes_name: raw_meta[str_name] for str_name, bytes_name in TimeVectorMetadataNames.str_keys_to_bytes_map.items() if str_name in raw_meta}

    @staticmethod
    def bytes_keys_to_str(raw_meta: dict[bytes, bytes]) -> dict[str, bytes]:
        return {str_name: raw_meta[bytes_name] for str_name, bytes_name in TimeVectorMetadataNames.str_keys_to_bytes_map.items() if bytes_name in raw_meta}

    @staticmethod
    def cast_value(value: str | bytes | None, cast_function: Callable | type) -> object | None:
        """
        Cast a string value into new type, but always return None if value is None or "None".

        Args:
            value (str | None): A string value or None.
            cast_function (Union[Callable, type]): Function or type with which to cast the value into.

        Raises:
            RuntimeError: If anything goes wrong in the cast_function.

        Returns:
            object|None: Value as new type or None.

        """
        if isinstance(value, bytes):
            if cast_function is bool:
                return None if value == b"None" else value == b"True"
            value = value.decode(encoding=TimeVectorMetadataNames.ENCODING)

        if value is None or value in {"None", ""}:  # Handle missing values
            return None
        try:
            return cast_function(value)
        except Exception as e:
            msg = f"Could not cast metadata value: {value}. Casting method: {cast_function}"
            raise RuntimeError(msg) from e

    @staticmethod
    def cast_strict_bool_value(value: str | bool | bytes) -> bool:
        if isinstance(value, bytes):
            return value == b"True"
        return bool(value)
