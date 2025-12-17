"""Define class for handling tables with Nodes."""

from typing import Any, ClassVar

import pandas as pd
import pandera as pa
from framcore.attributes import Price
from framcore.components import Node
from framcore.metadata import Meta
from numpy.typing import NDArray
from pandera.typing import DataFrame, Series

from framdata.database_names._attribute_metadata_names import _AttributeMetadataSchema
from framdata.database_names._base_names import _BaseComponentsNames
from framdata.database_names.validation_functions import (
    check_unit_is_str_for_attributes,
    dtype_str_int_float_none,
)


class NodesNames(_BaseComponentsNames):
    """Class representing the names and structure of nodes tables, and the convertion of the table to Node objects."""

    id_col = "NodeID"

    commodity_col = "Commodity"
    nice_name = "NiceName"
    price_col = "ExogenousPrice"
    profile_col = "PriceProfile"
    exogenous_col = "IsExogenous"

    columns: ClassVar[list[str]] = [id_col, nice_name, commodity_col, price_col, profile_col, exogenous_col]

    ref_columns: ClassVar[list[str]] = [price_col, profile_col]

    @staticmethod
    def create_component(
        row: NDArray,
        indices: dict[str, int],
        meta_columns: set[str],
        meta_data: pd.DataFrame,
        attribute_objects: dict[str, tuple[object, dict[str, Meta]]] | None = None,
    ) -> tuple[dict[str, Node], list[str]]:
        """
        Create a node object from direct parameters.

        Args:
            row (NDArray): Array containing the values of one table row, represeting one Node object.
            indices (list[str, int]): Mapping of table's Column names to the array's indices.
            meta_columns (list[str]): Set of columns which defines memberships in meta groups for aggregation.
            meta_data (pd.DataFrame): Dictionary containing at least unit of every column.
            attribute_objects (dict[str, tuple[object, dict[str, Meta]]], optional): NOT USED

        Returns:
            dict[str, Node]: Dictionary of node id and the Node object.

        """
        columns_to_parse = [
            NodesNames.price_col,
            NodesNames.profile_col,
        ]

        arg_user_code = NodesNames._parse_args(row, indices, columns_to_parse, meta_data)
        price = None
        if arg_user_code[NodesNames.price_col] is not None:
            price = Price(
                level=arg_user_code[NodesNames.price_col],
                profile=arg_user_code[NodesNames.profile_col],
            )

        node = Node(
            row[indices[NodesNames.commodity_col]],
            is_exogenous=row[indices[NodesNames.exogenous_col]],
            price=price,
        )
        NodesNames._add_meta(node, row, indices, meta_columns)
        return {str(row[indices[NodesNames.id_col]]): node}

    @staticmethod
    def get_attribute_data_schema() -> pa.DataFrameModel:
        """
        Get the Pandera DataFrameModel schema for attribute data in a Nodes file.

        Returns:
            pa.DataFrameModel: Pandera DataFrameModel schema for Nodes attribute data.

        """
        return NodesSchema

    @staticmethod
    def get_metadata_schema() -> pa.DataFrameModel:
        """
        Get the Pandera DataFrameModel schema for the metadata table in a Nodes file.

        Returns:
            pa.DataFrameModel: Pandera DataFrameModel schema for the Thermal metadata.

        """
        return NodesMetadataSchema

    @staticmethod
    def _get_unique_check_descriptions() -> dict[str, tuple[str, bool]]:
        """
        Retrieve a dictionary with descriptons of validation checks that are specific to the Nodes schemas.

        Returns:
            dict[str, tuple[str, bool]]: A dictionary where:
                - Keys (str): The name of the validation check method.
                - Values (tuple[str, bool]):
                    - The first element (str) provides a concise and user-friendly description of the check. E.g. what
                      caused the validation error or what is required for the check to pass.
                    - The second element (bool) indicates whether the check is a warning (True) or an error (False).


        """
        return {
            NodesSchema.check_exogenous_price.__name__: ("Missing price value for exogenous Node.", True),
        }

    @staticmethod
    def _format_unique_checks(errors: pd.DataFrame) -> pd.DataFrame:
        """
        Format the error DataFrame according to the validation checks that are specific to the Nodes schemas.

        Args:
            errors (pd.DataFrame): The error DataFrame containing validation errors.

        Returns:
            pd.DataFrame: The updated error DataFrame with formatted rows for unique validation checks.

        """
        if NodesSchema.check_exogenous_price.__name__ in errors[NodesNames.COL_CHECK].to_numpy():
            check_rows = errors.loc[errors[NodesNames.COL_CHECK] == NodesSchema.check_exogenous_price.__name__]
            errors = errors[~(errors[NodesNames.COL_CHECK] == NodesSchema.check_exogenous_price.__name__)]
            price_exogenous_cols = [NodesNames.id_col, NodesNames.price_col, NodesNames.exogenous_col]
            check_description_str = check_rows[NodesNames.COL_CHECK_DESC].unique()[0]
            price_exogenous_rows = []

            for idx in check_rows[NodesNames.COL_IDX].unique():
                check_case = check_rows[check_rows[NodesNames.COL_IDX] == idx]

                for col in price_exogenous_cols:
                    if col not in list(check_case[NodesNames.COL_COLUMN].unique()):
                        price_exogenous_rows.append(
                            [
                                col,
                                NodesSchema.check_exogenous_price.__name__,
                                None,
                                idx,
                                check_description_str,
                                True,
                            ],
                        )
            errors = pd.concat([errors, pd.DataFrame(price_exogenous_rows, columns=errors.columns)], ignore_index=True)
        return errors


class NodesSchema(pa.DataFrameModel):
    """Standard Pandera DataFrameModel schema for attribute data in the Nodes files."""

    NodeID: Series[str] = pa.Field(unique=True, nullable=False)
    Commodity: Series[str] = pa.Field(nullable=False)
    ExogenousPrice: Series[Any] = pa.Field(nullable=True)
    PriceProfile: Series[Any] = pa.Field(nullable=True)
    IsExogenous: Series[bool] = pa.Field(nullable=False)

    @pa.check(NodesNames.price_col, NodesNames.profile_col)
    @classmethod
    def dtype_str_int_float_none(cls, series: Series[Any]) -> Series[bool]:
        """Check if values in the series are of datatype: str, int, float or None."""
        return dtype_str_int_float_none(series)

    @pa.dataframe_check
    @classmethod
    def check_exogenous_price(cls, df: DataFrame) -> Series[bool]:
        """Check that all elastic demand values are present if one or more is."""
        price = df[NodesNames.price_col]
        exogenous = df[NodesNames.exogenous_col]
        return ~pd.Series(price.isna() & exogenous)  # return should be false when price is None and Node is exogenous.


class NodesMetadataSchema(_AttributeMetadataSchema):
    """Standard Pandera DataFrameModel schema for metadata in the Nodes files."""

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
        return check_unit_is_str_for_attributes(df, [NodesNames.price_col])


class PowerNodesNames(NodesNames):
    """Class representing the names and structure of power nodes tables."""

    filename = "Power.Nodes"


class FuelNodesNames(NodesNames):
    """Class representing the names and structure of fuel nodes tables."""

    filename = "Fuel.Nodes"

    emission_coefficient_col = "EmissionCoefficient"
    tax_col = "Tax"  # deprecated?


class EmissionNodesNames(NodesNames):
    """Class representing the names and structure of emission nodes tables."""

    filename = "Emission.Nodes"

    tax_col = "Tax"  # deprecated?
