"""Contains classes defining the demand table and validations."""

from typing import Any, ClassVar

import pandas as pd
import pandera as pa
from framcore.attributes import ElasticDemand, Elasticity, MaxFlowVolume, Price, ReservePrice
from framcore.components import Demand
from framcore.metadata import Meta
from numpy.typing import NDArray
from pandera.typing import DataFrame, Series

from framdata.database_names._attribute_metadata_names import _AttributeMetadataSchema
from framdata.database_names._base_names import _BaseComponentsNames
from framdata.database_names.validation_functions import (
    check_unit_is_str_for_attributes,
    dtype_str_int_float,
    dtype_str_int_float_none,
    numeric_values_are_between_or_equal_to,
    numeric_values_greater_than_or_equal_to,
    numeric_values_less_than_or_equal_to,
)


class DemandNames(_BaseComponentsNames):
    """Container class for describing the demand attribute table's names, structure, and convertion to Demand Component."""

    id_col = "ConsumerID"
    node_col = "PowerNode"
    reserve_price_col = "ReservePrice"
    price_elasticity_col = "PriceElasticity"
    min_price_col = "MinPriceLimit"
    max_price_col = "MaxPriceLimit"
    normal_price_col = "NormalPrice"
    capacity_profile_col = "CapacityProfile"
    temperature_profile_col = "TemperatureProfile"
    capacity_col = "Capacity"

    columns: ClassVar[list[str]] = [
        id_col,
        node_col,
        reserve_price_col,
        price_elasticity_col,
        min_price_col,
        max_price_col,
        normal_price_col,
        capacity_profile_col,
        temperature_profile_col,
        capacity_col,
    ]

    ref_columns: ClassVar[list[str]] = [
        node_col,
        reserve_price_col,
        price_elasticity_col,
        min_price_col,
        max_price_col,
        normal_price_col,
        capacity_profile_col,
        temperature_profile_col,
        capacity_col,
    ]

    @staticmethod
    def create_component(
        row: NDArray,
        indices: dict[str, int],
        meta_columns: set[str],
        meta_data: pd.DataFrame,
        attribute_objects: dict[str, tuple[object, dict[str, Meta]]] | None = None,
    ) -> dict[str, Demand]:
        """
        Create a Demand component from a table row in the Demand.Consumers file.

        Args:
            row (NDArray): Array containing the values of one table row, represeting one Demand object.
            indices (list[str, int]): Mapping of table's Column names to the array's indices.
            meta_columns (list[str]): Set of columns which defines memberships in meta groups for aggregation.
            meta_data (pd.DataFrame): Dictionary containing at least unit of every column.
            attribute_objects (dict[str, tuple[object, dict[str, Meta]]], optional): NOT USED

        Returns:
            dict[str, Demand]: A dictionary with the consumer_id as key and the demand component as value.

        """
        elastic_demand_cols = [
            DemandNames.price_elasticity_col,
            DemandNames.min_price_col,
            DemandNames.max_price_col,
            DemandNames.normal_price_col,
        ]
        columns_to_parse = [
            DemandNames.reserve_price_col,
            DemandNames.capacity_profile_col,
            DemandNames.temperature_profile_col,
            DemandNames.capacity_col,
        ]
        columns_to_parse.extend(elastic_demand_cols)

        arg_user_code = DemandNames._parse_args(row, indices, columns_to_parse, meta_data)

        elastic_demand_values = [value for key, value in arg_user_code.items() if key in elastic_demand_cols]
        if all(value is not None for value in elastic_demand_values):
            elastic_demand = ElasticDemand(
                price_elasticity=Elasticity(level=arg_user_code[DemandNames.price_elasticity_col]),
                min_price=Price(level=arg_user_code[DemandNames.min_price_col]),
                normal_price=Price(level=arg_user_code[DemandNames.normal_price_col]),
                max_price=Price(level=arg_user_code[DemandNames.max_price_col]),
            )
            reserve_price = None
        elif arg_user_code[DemandNames.reserve_price_col] is not None:
            elastic_demand = None
            reserve_price = ReservePrice(level=arg_user_code[DemandNames.reserve_price_col])
        else:
            elastic_demand = None
            reserve_price = None
        demand = Demand(
            node=row[indices[DemandNames.node_col]],
            capacity=MaxFlowVolume(
                level=arg_user_code[DemandNames.capacity_col],
                profile=arg_user_code[DemandNames.capacity_profile_col],
            ),
            reserve_price=reserve_price,
            elastic_demand=elastic_demand,
            temperature_profile=arg_user_code[DemandNames.temperature_profile_col],
        )
        DemandNames._add_meta(demand, row, indices, meta_columns)

        return {row[indices[DemandNames.id_col]]: demand}

    @staticmethod
    def get_attribute_data_schema() -> pa.DataFrameModel:
        """
        Get the Pandera DataFrameModel schema for attribute data in the Demand.Consumers file.

        Returns:
            DemandSchema (pa.DataFrameModel): Pandera DataFrameModel schema for Demand attribute data.

        """
        return DemandSchema

    @staticmethod
    def get_metadata_schema() -> pa.DataFrameModel:
        """
        Get the Pandera DataFrameModel schema for metadata in the Demand.Consumers file.

        Returns:
            DemandMetadataSchema (pa.DataFrameModel): Pandera DataFrameModel schema for Demand metadata.

        """
        return DemandMetadataSchema

    @staticmethod
    def _get_unique_check_descriptions() -> dict[str, tuple[str, bool]]:
        """
        Retrieve a dictionary with descriptons of validation checks that are specific to the Demand schemas.

        Returns:
            dict[str, tuple[str, bool]]: A dictionary where:
                - Keys (str): The name of the validation check method.
                - Values (tuple[str, bool]):
                    - The first element (str) provides a concise and user-friendly description of the check. E.g. what
                      caused the validation error or what is required for the check to pass.
                    - The second element (bool) indicates whether the check is a warning (True) or an error (False).

        """
        return {
            DemandSchema.check_elastic_demand.__name__: ("Missing elastic demand value.", True),
        }

    @staticmethod
    def _format_unique_checks(errors: pd.DataFrame) -> pd.DataFrame:
        """
        Format the error DataFrame according to the validation checks that are specific to the Demand schemas.

        This method processes validation errors that come from a dataframe-level check on elastic demand columns in the
        attribute data schema. The default reporting on failed dataframe-level checks in Pandera's standard error
        reports DataFrame (errors) is not very user-friendly. It can contain uneccassary rows about columns that are not
        relevant to the check and will not include rows about the columns relevant to the check if those columns have
        missing values. This method removes uneccassary rows from the error dataframe and ensures that rows with
        information abot the elastic demand columns that fail the check are included.

        Args:
            errors (pd.DataFrame): DataFrame containing validation errors. Pandera's standard error reports DataFrame.

        Returns:
            pd.DataFrame: The updated error DataFrame with formatted rows for unique validation checks.

        """
        if DemandSchema.check_elastic_demand.__name__ in errors[DemandNames.COL_CHECK].to_numpy():
            check_rows = errors.loc[errors[DemandNames.COL_CHECK] == DemandSchema.check_elastic_demand.__name__]
            errors = errors[~(errors[DemandNames.COL_CHECK] == DemandSchema.check_elastic_demand.__name__)]
            elastic_demand_columns = [
                DemandNames.price_elasticity_col,
                DemandNames.min_price_col,
                DemandNames.max_price_col,
                DemandNames.normal_price_col,
            ]
            check_description_str = check_rows[DemandNames.COL_CHECK_DESC].unique()[0]
            elastic_demand_rows = []
            for idx in check_rows[DemandNames.COL_IDX].unique():
                check_case = check_rows[check_rows[DemandNames.COL_IDX] == idx]
                for col in elastic_demand_columns:
                    if col not in list(check_case[DemandNames.COL_COLUMN].unique()):
                        elastic_demand_rows.append(
                            [
                                col,
                                DemandSchema.check_elastic_demand.__name__,
                                None,
                                idx,
                                check_description_str,
                                True,
                            ],
                        )
            errors = pd.concat([errors, pd.DataFrame(elastic_demand_rows, columns=errors.columns)], ignore_index=True)
        return errors


class DemandSchema(pa.DataFrameModel):
    """Pandera DataFrameModel schema for attribute data in the Demand.Consumers file."""

    ConsumerID: Series[str] = pa.Field(unique=True, nullable=False)
    PowerNode: Series[str] = pa.Field(nullable=False)
    ReservePrice: Series[Any] = pa.Field(nullable=True)
    PriceElasticity: Series[Any] = pa.Field(nullable=True)
    MinPriceLimit: Series[Any] = pa.Field(nullable=True)
    MaxPriceLimit: Series[Any] = pa.Field(nullable=True)
    NormalPrice: Series[Any] = pa.Field(nullable=True)
    CapacityProfile: Series[Any] = pa.Field(nullable=True)
    TemperatureProfile: Series[Any] = pa.Field(nullable=True)
    Capacity: Series[Any] = pa.Field(nullable=False)

    @pa.check(DemandNames.capacity_col)
    @classmethod
    def dtype_str_int_float(cls, series: Series[Any]) -> Series[bool]:
        """Check if values in the series are of datatype: str, int or float."""
        return dtype_str_int_float(series)

    @pa.check(
        DemandNames.reserve_price_col,
        DemandNames.price_elasticity_col,
        DemandNames.min_price_col,
        DemandNames.max_price_col,
        DemandNames.normal_price_col,
        DemandNames.capacity_profile_col,
        DemandNames.temperature_profile_col,
    )
    @classmethod
    def dtype_str_int_float_none(cls, series: Series[Any]) -> Series[bool]:
        """Check if values in the series are of datatype: str, int, float or None."""
        return dtype_str_int_float_none(series)

    @pa.check(DemandNames.price_elasticity_col)
    @classmethod
    def numeric_values_less_than_or_equal_to_0(cls, series: Series[Any]) -> Series[bool]:
        """Check if numeric values in the series are less than or equal to zero."""
        return numeric_values_less_than_or_equal_to(series, 0)

    @pa.check(
        DemandNames.reserve_price_col,
        DemandNames.min_price_col,
        DemandNames.max_price_col,
        DemandNames.normal_price_col,
        DemandNames.capacity_col,
    )
    @classmethod
    def numeric_values_greater_than_or_equal_to_0(cls, series: Series[Any]) -> Series[bool]:
        """Check if numeric values in the series are greater than or equal to zero."""
        return numeric_values_greater_than_or_equal_to(series, 0)

    @pa.check(DemandNames.capacity_profile_col)
    @classmethod
    def numeric_values_are_between_or_equal_to_0_and_1(cls, series: Series[Any]) -> Series[bool]:
        """Check if numeric values in the series are between zero and one or equal to zero and one."""
        return numeric_values_are_between_or_equal_to(series, 0, 1)

    @pa.dataframe_check
    @classmethod
    def check_elastic_demand(cls, df: DataFrame) -> Series[bool]:
        """Check that all elastic demand values are present if one or more is."""
        elastic_demand = df[
            [
                DemandNames.price_elasticity_col,
                DemandNames.min_price_col,
                DemandNames.max_price_col,
                DemandNames.normal_price_col,
            ]
        ]

        check = elastic_demand.apply(
            lambda row: all(value is not None for value in row) if any(value is not None for value in row) else True,
            axis=1,
        ).tolist()
        return pd.Series(check)

    class Config:
        """Schema-wide configuration for the DemandSchema class."""

        unique_column_names = True


class DemandMetadataSchema(_AttributeMetadataSchema):
    """Pandera DataFrameModel schema for metadata in the Demand.Consumers file."""

    @pa.dataframe_check
    @classmethod
    def check_unit_is_str_for_attributes(cls, df: pd.DataFrame) -> Series[bool]:
        """
        Check that the 'unit' value is a string for the row where 'attribute' is 'Capacity'.

        Args:
            df (Dataframe): DataFrame used to check value for "unit".

        Returns:
            Series[bool]: Series of boolean values detonating if each element has passed the check.

        """
        return check_unit_is_str_for_attributes(df, [DemandNames.capacity_col])
