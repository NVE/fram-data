"""Describe attribute table metadata."""

from typing import Any, ClassVar

import pandas as pd
import pandera as pa
from pandera.typing import Series


class _AttributeMetadataNames:
    """Describe names and structure for attribute tables' metadata."""

    attribute = "Attribute"
    reference = "Reference"
    unit = "Unit"

    description = "Description"

    is_max_level = "IsMaxLevel"
    is_zero_one_profile = "IsZeroOneProfile"

    # reference period
    start_year = "RefPeriodStartYear"
    num_years = "RefPeriodNumberOfYears"

    dtypes: ClassVar[dict[str, type]] = {
        attribute: str,
        reference: str,
        unit: str,
        is_max_level: bool,
        is_zero_one_profile: bool,
        start_year: int,
        num_years: int,
    }

    @staticmethod
    def get_meta(meta_data: pd.DataFrame, meta_col: str, attribute_name: str) -> str:
        """
        Get the unit of an attribute from the meta data.

        Args:
            meta_data (pd.DataFrame): The meta data for the thermal unit.
            meta_col (str): Metadata column.
            attribute_name (str): The name of the attribute.

        Returns:
            str: The unit of the attribute.

        Note:
            The method assumes that the meta data contains a column with the name "attribute" and
            a "unit" column. This will be validated with pandera schema before running the code.

        """
        filtered_meta_data = meta_data[meta_data[_AttributeMetadataNames.attribute] == attribute_name]
        return filtered_meta_data.iloc[0][meta_col]


class _AttributeMetadataSchema(pa.DataFrameModel):
    """Standard Pandera DataFrameModel schema for Metadata tables in the NVE database."""

    Attribute: Series[str] = pa.Field(unique=True)
    Unit: Series[str] = pa.Field(nullable=True)

    RefPeriodStartYear: Series[Any] = pa.Field(nullable=True)
    RefPeriodNumberOfYears: Series[Any] = pa.Field(nullable=True)

    IsMaxLevel: Series[Any] = pa.Field(nullable=True)
    IsZeroOneProfile: Series[Any] = pa.Field(nullable=True)

    pa.check(_AttributeMetadataNames.start_year, _AttributeMetadataNames.num_years)

    @classmethod
    def dtype_int_none(cls, series: Series[Any]) -> Series[bool]:
        return series.apply(lambda value: isinstance(value, int | type(None)))

    pa.check(_AttributeMetadataNames.is_max_level, _AttributeMetadataNames.is_zero_one_profile)

    @classmethod
    def dtype_bool_none(cls, series: Series[Any]) -> Series[bool]:
        return series.apply(lambda value: isinstance(value, bool | type(None)))

    class Config:
        """Configuration for the DemandSchema class."""

        unique_column_names: ClassVar[list] = [_AttributeMetadataNames.attribute, _AttributeMetadataNames.unit]
