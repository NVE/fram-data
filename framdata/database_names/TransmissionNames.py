"""
Defines the TransmissionNames class and related Pandera schemas.

These describe validate Transmission attributes and metadata tables in the energy model database.
"""

from typing import Any, ClassVar

import pandas as pd
import pandera as pa
from framcore.attributes import Cost, Loss, MaxFlowVolume, Proportion
from framcore.components import Transmission
from framcore.metadata import Meta
from numpy.typing import NDArray
from pandera.typing import Series

from framdata.database_names._attribute_metadata_names import _AttributeMetadataSchema
from framdata.database_names._base_names import _BaseComponentsNames
from framdata.database_names.validation_functions import (
    check_unit_is_str_for_attributes,
    dtype_str_int_float,
    dtype_str_int_float_none,
    numeric_values_are_between_or_equal_to,
    numeric_values_greater_than_or_equal_to,
)


class TransmissionNames(_BaseComponentsNames):
    """Container class for describing the Transmission attribute table's names and structure."""

    id_col = "TransmissionID"
    from_node_col = "FromNode"
    to_node_col = "ToNode"
    capacity_col = "Capacity"
    loss_col = "Loss"
    tariff_col = "Tariff"
    max_op_bound_col = "MaxOperationalBound"
    min_op_bound_col = "MinOperationalBound"
    ramp_up_col = "RampUp"
    ramp_down_col = "RampDown"

    columns: ClassVar[list[str]] = [
        id_col,
        from_node_col,
        to_node_col,
        capacity_col,
        loss_col,
        tariff_col,
        max_op_bound_col,
        min_op_bound_col,
        ramp_up_col,
        ramp_down_col,
    ]

    ref_columns: ClassVar[list[str]] = [
        from_node_col,
        to_node_col,
        capacity_col,
        loss_col,
        tariff_col,
        max_op_bound_col,
        min_op_bound_col,
        ramp_up_col,
        ramp_down_col,
    ]

    @staticmethod
    def create_component(
        row: NDArray,
        indices: dict[str, int],
        meta_columns: set[str],
        meta_data: pd.DataFrame,
        attribute_objects: dict[str, tuple[object, dict[str, Meta]]] | None = None,
    ) -> dict[str, Transmission]:
        """
        Create a transmission unit component.

        Args:
            row (NDArray): Array containing the values of one table row, represeting one Transmission object.
            indices (list[str, int]): Mapping of table's Column names to the array's indices.
            meta_columns (set[str]): Set of columns used to tag object with memberships.
            meta_data (pd.DataFrame): Dictionary containing at least unit of every column.
            attribute_objects (dict[str, tuple[object, dict[str, Meta]]] | None, optional): NOT USED

        Returns:
            dict[str, Transmission]: A dictionary with the transmission_id as key and the transmission unit as value.

        """
        columns_to_parse = [
            TransmissionNames.capacity_col,
            TransmissionNames.loss_col,
            TransmissionNames.tariff_col,
            TransmissionNames.max_op_bound_col,
            TransmissionNames.min_op_bound_col,
            TransmissionNames.ramp_up_col,
            TransmissionNames.ramp_down_col,
        ]

        arg_user_code = TransmissionNames._parse_args(row, indices, columns_to_parse, meta_data)

        ramp_up = None if arg_user_code[TransmissionNames.ramp_up_col] is None else Proportion(level=arg_user_code[TransmissionNames.ramp_up_col])
        ramp_down = None if arg_user_code[TransmissionNames.ramp_down_col] is None else Proportion(level=arg_user_code[TransmissionNames.ramp_down_col])
        loss = None if arg_user_code[TransmissionNames.loss_col] is None else Loss(level=arg_user_code[TransmissionNames.loss_col])

        tariff = None if arg_user_code[TransmissionNames.tariff_col] is None else Cost(level=arg_user_code[TransmissionNames.tariff_col])

        min_capacity = (
            None
            if arg_user_code[TransmissionNames.min_op_bound_col] is None
            else MaxFlowVolume(
                level=arg_user_code[TransmissionNames.capacity_col],
                profile=arg_user_code[TransmissionNames.min_op_bound_col],
            )
        )

        transmission = Transmission(
            from_node=row[indices[TransmissionNames.from_node_col]],
            to_node=row[indices[TransmissionNames.to_node_col]],
            max_capacity=MaxFlowVolume(
                level=arg_user_code[TransmissionNames.capacity_col],
                profile=arg_user_code[TransmissionNames.max_op_bound_col],
            ),
            min_capacity=min_capacity,
            loss=loss,
            tariff=tariff,
            ramp_up=ramp_up,
            ramp_down=ramp_down,
        )
        TransmissionNames._add_meta(transmission, row, indices, meta_columns)

        return {row[indices[TransmissionNames.id_col]]: transmission}

    @staticmethod
    def get_attribute_data_schema() -> pa.DataFrameModel:
        """
        Get the Pandera DataFrameModel schema for attribute data in the Transmission.Grid file.

        Returns:
            pa.DataFrameModel: Pandera DataFrameModel schema for Transmission attribute data.

        """
        return TransmissionSchema

    @staticmethod
    def get_metadata_schema() -> pa.DataFrameModel:
        """
        Get the Pandera DataFrameModel schema for the metadata table in the Transmission.Grid file.

        Returns:
            pa.DataFrameModel: Pandera DataFrameModel schema for the Transmission metadata.

        """
        return TransmissionMetadataSchema

    @staticmethod
    def _get_unique_check_descriptions() -> dict[str, tuple[str, bool]]:
        """
        Retrieve a dictionary with descriptons of validation checks that are specific to the Transmission schemas.

        Returns:
            dict[str, tuple[str, bool]]: A dictionary where:
                - Keys (str): The name of the validation check method.
                - Values (tuple[str, bool]):
                    - The first element (str) provides a concise and user-friendly description of the check. E.g. what
                      caused the validation error or what is required for the check to pass.
                    - The second element (bool) indicates whether the check is a warning (True) or an error (False).


        """
        return {
            "check_internal_line_error": ("Transmission line is internal (FromNode equals ToNode).", False),
        }

    @staticmethod
    def _format_unique_checks(errors: pd.DataFrame) -> pd.DataFrame:
        """
        Format the error DataFrame according to the validation checks that are specific to the Transmission schemas.

        Args:
            errors (pd.DataFrame): The error DataFrame containing validation errors.

        Returns:
            pd.DataFrame: The updated error DataFrame with formatted rows for unique validation checks.

        """
        check_name = "check_internal_line_error"
        if check_name in errors[TransmissionNames.COL_CHECK].to_numpy():
            check_rows = errors.loc[
                (errors[TransmissionNames.COL_CHECK] == check_name)
                & (
                    errors[TransmissionNames.COL_COLUMN].isin(
                        [TransmissionNames.from_node_col, TransmissionNames.to_node_col],
                    )
                )
            ]
            check_rows.loc[:, TransmissionNames.COL_COLUMN] = f"{TransmissionNames.from_node_col}, {TransmissionNames.to_node_col}"
            check_rows = check_rows.drop_duplicates()
            errors = errors[~(errors[TransmissionNames.COL_CHECK] == check_name)]
            errors = pd.concat([errors, check_rows], ignore_index=True)

        return errors


class TransmissionSchema(pa.DataFrameModel):
    """Pandera DataFrameModel schema for attribute data in the Transmission.Grid file."""

    TransmissionID: Series[str] = pa.Field(unique=True, nullable=False)
    FromNode: Series[str] = pa.Field(nullable=False)
    ToNode: Series[str] = pa.Field(nullable=False)
    Capacity: Series[Any] = pa.Field(nullable=False)
    Loss: Series[Any] = pa.Field(nullable=True)
    Tariff: Series[Any] = pa.Field(nullable=True)
    MaxOperationalBound: Series[Any] = pa.Field(nullable=True)
    MinOperationalBound: Series[Any] = pa.Field(nullable=True)
    RampUp: Series[Any] = pa.Field(nullable=True)
    RampDown: Series[Any] = pa.Field(nullable=True)

    @pa.check(TransmissionNames.capacity_col)
    @classmethod
    def dtype_str_int_float(cls, series: Series[Any]) -> Series[bool]:
        """Check if values in the series are of datatype: str, int or float."""
        return dtype_str_int_float(series)

    @pa.check(
        TransmissionNames.loss_col,
        TransmissionNames.tariff_col,
        TransmissionNames.max_op_bound_col,
        TransmissionNames.min_op_bound_col,
        TransmissionNames.ramp_up_col,
        TransmissionNames.ramp_down_col,
    )
    @classmethod
    def dtype_str_int_float_none(cls, series: Series[Any]) -> Series[bool]:
        """Check if values in the series are of datatype: str, int, float or None."""
        return dtype_str_int_float_none(series)

    @pa.check(TransmissionNames.capacity_col)
    @classmethod
    def numeric_values_greater_than_or_equal_to_0(cls, series: Series[Any]) -> Series[bool]:
        """Check if numeric values in the series are greater than or equal to zero."""
        return numeric_values_greater_than_or_equal_to(series, 0)

    @pa.check(TransmissionNames.loss_col)
    @classmethod
    def numeric_values_are_between_or_equal_to_0_and_1(cls, series: Series[Any]) -> Series[bool]:
        """Check if numeric values in the series are between zero and one or equal to zero and one."""
        return numeric_values_are_between_or_equal_to(series, 0, 1)

    @pa.dataframe_check
    @classmethod
    def check_internal_line_error(cls, dataframe: pd.DataFrame) -> Series[bool]:
        """
        Raise warning if origin node is the same as destination node, in which case we have an internal line.

        Args:
            dataframe (pd.DataFrame): DataFrame to check.

        Returns:
            Series[bool]: Series of boolean values denoting if each element has passed the check.

        """
        return dataframe[TransmissionNames.from_node_col] != dataframe[TransmissionNames.to_node_col]

    class Config:
        """Schema-wide configuration for the DemandSchema class."""

        unique_column_names = True


class TransmissionMetadataSchema(_AttributeMetadataSchema):
    """Pandera DataFrameModel schema for metadata in the Transmission.Grid file."""

    @pa.dataframe_check
    @classmethod
    def check_unit_is_str_for_attributes(cls, df: pd.DataFrame) -> Series[bool]:
        """
        Check that the 'unit' value is a string for the rows where 'attribute' is 'Capacity' and 'Loss'.

        Args:
            df (Dataframe): DataFrame used to check value for "unit".

        Returns:
            Series[bool]: Series of boolean values detonating if each element has passed the check.

        """
        return check_unit_is_str_for_attributes(df, [TransmissionNames.capacity_col, TransmissionNames.tariff_col])
