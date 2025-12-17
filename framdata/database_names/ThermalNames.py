"""Classes defining Thermal tables."""

from typing import Any, ClassVar

import pandas as pd
import pandera as pa
from framcore.attributes import Conversion, Cost, Efficiency, Hours, MaxFlowVolume, Proportion, StartUpCost
from framcore.components import Thermal
from framcore.metadata import Meta
from numpy.typing import NDArray
from pandera.typing import Series

from framdata.database_names._attribute_metadata_names import _AttributeMetadataSchema
from framdata.database_names._base_names import _BaseComponentsNames
from framdata.database_names.nodes_names import FuelNodesNames
from framdata.database_names.validation_functions import (
    check_unit_is_str_for_attributes,
    dtype_str_int_float,
    dtype_str_int_float_none,
    numeric_values_greater_than_or_equal_to,
)


class ThermalNames(_BaseComponentsNames):
    """Container class for describing the Thermal attribute table's names and structure."""

    id_col = "ThermalID"
    main_unit_col = "MainUnit"
    nice_name_col = "NiceName"
    power_node_col = "PowerNode"
    fuel_node_col = "FuelNode"
    emission_node_col = "EmissionNode"
    emission_coeff_col = "EmissionCoefficient"
    type_col = "Type"
    capacity_col = "Capacity"
    full_load_col = "FullLoadEfficiency"
    part_load_col = "PartLoadEfficiency"
    voc_col = "VOC"
    start_costs_col = "StartCosts"
    start_hours_col = "StartHours"
    min_stable_load_col = "MinStableLoad"
    min_op_bound_col = "MinOperationalBound"
    max_op_bound_col = "MaxOperationalBound"
    ramp_up_col = "RampUp"
    ramp_down_col = "RampDown"

    # Should include rampup/down data in Thermal, when we get data for this
    columns: ClassVar[list[str]] = [
        id_col,
        nice_name_col,
        type_col,
        main_unit_col,
        power_node_col,
        fuel_node_col,
        emission_node_col,
        capacity_col,
        full_load_col,
        part_load_col,
        voc_col,
        start_costs_col,
        start_hours_col,
        min_stable_load_col,
        min_op_bound_col,
        max_op_bound_col,
        emission_coeff_col,
    ]

    ref_columns: ClassVar[list[str]] = [
        power_node_col,
        fuel_node_col,
        emission_node_col,
        capacity_col,
        full_load_col,
        part_load_col,
        voc_col,
        start_costs_col,
        start_hours_col,
        min_stable_load_col,
        min_op_bound_col,
        max_op_bound_col,
        emission_coeff_col,
    ]

    @staticmethod
    def create_component(
        row: NDArray,
        indices: dict[str, int],
        meta_columns: set[str],
        meta_data: pd.DataFrame,
        attribute_objects: dict[str, tuple[object, dict[str, Meta]]] | None = None,
    ) -> dict[str, Thermal]:
        """
        Create a thermal unit component.

        Args:
            row (NDArray): Array containing the values of one table row, represeting one Thermal object.
            indices (list[str, int]): Mapping of table's Column names to the array's indices.
            meta_columns (set[str]): Set of columns used to tag object with memberships.
            meta_data (pd.DataFrame): Dictionary containing at least unit of every column.
            attribute_objects (dict[str, tuple[object, dict[str, Meta]]], optional): NOT USED

        Returns:
            dict[str, Thermal]: A dictionary with the thermal_id as key and the thermal unit as value.

        """
        columns_to_parse = [
            ThermalNames.emission_node_col,
            ThermalNames.capacity_col,
            ThermalNames.full_load_col,
            ThermalNames.part_load_col,
            ThermalNames.voc_col,
            ThermalNames.start_costs_col,
            ThermalNames.start_hours_col,
            ThermalNames.min_stable_load_col,
            ThermalNames.min_op_bound_col,
            ThermalNames.max_op_bound_col,
            ThermalNames.emission_coeff_col,
        ]

        arg_user_code = ThermalNames._parse_args(row, indices, columns_to_parse, meta_data)

        no_start_up_costs_condition = (
            (arg_user_code[ThermalNames.start_costs_col] is None)
            or (arg_user_code[ThermalNames.min_stable_load_col] is None)
            or (arg_user_code[ThermalNames.start_hours_col] is None)
            or (arg_user_code[ThermalNames.part_load_col] is None)
        )
        start_up_cost = (
            None
            if no_start_up_costs_condition
            else StartUpCost(
                startup_cost=Cost(level=arg_user_code[ThermalNames.start_costs_col]),
                min_stable_load=Proportion(level=arg_user_code[ThermalNames.min_stable_load_col]),
                start_hours=Hours(level=arg_user_code[ThermalNames.start_hours_col]),
                part_load_efficiency=Efficiency(level=arg_user_code[ThermalNames.part_load_col]),
            )
        )

        voc = (
            None
            if arg_user_code[ThermalNames.voc_col] is None
            else Cost(
                level=arg_user_code[ThermalNames.voc_col],
                profile=None,
            )
        )

        min_capacity = (
            None
            if arg_user_code[ThermalNames.min_op_bound_col] is None
            else MaxFlowVolume(
                level=arg_user_code[ThermalNames.capacity_col],
                profile=arg_user_code[ThermalNames.min_op_bound_col],
            )
        )

        thermal = Thermal(
            power_node=row[indices[ThermalNames.power_node_col]],
            fuel_node=row[indices[ThermalNames.fuel_node_col]],
            efficiency=Efficiency(level=arg_user_code[ThermalNames.full_load_col]),
            emission_node=row[indices[ThermalNames.emission_node_col]],
            emission_coefficient=Conversion(level=arg_user_code[FuelNodesNames.emission_coefficient_col]),
            max_capacity=MaxFlowVolume(
                level=arg_user_code[ThermalNames.capacity_col],
                profile=arg_user_code[ThermalNames.max_op_bound_col],
            ),
            min_capacity=min_capacity,
            voc=voc,
            startupcost=start_up_cost,
        )
        ThermalNames._add_meta(thermal, row, indices, meta_columns)

        return {row[indices[ThermalNames.id_col]]: thermal}

    @staticmethod
    def get_attribute_data_schema() -> pa.DataFrameModel:
        """
        Get the Pandera DataFrameModel schema for attribute data in the Thermal.Generators file.

        Returns:
            pa.DataFrameModel: Pandera DataFrameModel schema for Thermal attribute data.

        """
        return ThermalSchema

    @staticmethod
    def get_metadata_schema() -> pa.DataFrameModel:
        """
        Get the Pandera DataFrameModel schema for the metadata table in the Thermal.Generators file.

        Returns:
            pa.DataFrameModel: Pandera DataFrameModel schema for the Thermal metadata.

        """
        return ThermalMetadataSchema

    @staticmethod
    def _get_unique_check_descriptions() -> dict[str, tuple[str, bool]]:
        """
        Retrieve a dictionary with descriptons of validation checks that are specific to the Thermal schemas.

        Returns:
            dict[str, tuple[str, bool]]: A dictionary where:
                - Keys (str): The name of the validation check method.
                - Values (tuple[str, bool]):
                    - The first element (str) provides a concise and user-friendly description of the check. E.g. what
                      caused the validation error or what is required for the check to pass.
                    - The second element (bool) indicates whether the check is a warning (True) or an error (False).


        """
        return None

    @staticmethod
    def _format_unique_checks(errors: pd.DataFrame) -> pd.DataFrame:
        """
        Format the error DataFrame according to the validation checks that are specific to the Thermal schemas.

        Args:
            errors (pd.DataFrame): The error DataFrame containing validation errors.

        Returns:
            pd.DataFrame: The updated error DataFrame with formatted rows for unique validation checks.

        """
        return None


class ThermalSchema(pa.DataFrameModel):
    """Pandera DataFrameModel schema for attribute data in the Thermal.Generators file."""

    ThermalID: Series[str] = pa.Field(unique=True, nullable=False)
    PowerNode: Series[str] = pa.Field(nullable=False)
    FuelNode: Series[str] = pa.Field(nullable=False)
    EmissionCoefficient: Series[Any] = pa.Field(nullable=True)
    EmissionNode: Series[str] = pa.Field(nullable=True)
    Capacity: Series[Any] = pa.Field(nullable=False)
    FullLoadEfficiency: Series[Any] = pa.Field(nullable=True)
    PartLoadEfficiency: Series[Any] = pa.Field(nullable=True)
    VOC: Series[Any] = pa.Field(nullable=True)
    StartCosts: Series[Any] = pa.Field(nullable=True)
    StartHours: Series[Any] = pa.Field(nullable=True)
    MinStableLoad: Series[Any] = pa.Field(nullable=True)
    MinOperationalBound: Series[Any] = pa.Field(nullable=True)
    MaxOperationalBound: Series[Any] = pa.Field(nullable=True)
    RampUp: Series[Any] = pa.Field(nullable=True)
    RampDown: Series[Any] = pa.Field(nullable=True)

    @pa.check(ThermalNames.capacity_col)
    @classmethod
    def dtype_str_int_float(cls, series: Series[Any]) -> Series[bool]:
        """Check if values in the series are of datatype: str, int or float."""
        return dtype_str_int_float(series)

    @pa.check(
        ThermalNames.emission_coeff_col,
        ThermalNames.full_load_col,
        ThermalNames.part_load_col,
        ThermalNames.voc_col,
        ThermalNames.start_costs_col,
        ThermalNames.start_hours_col,
        ThermalNames.min_stable_load_col,
        ThermalNames.max_op_bound_col,
        ThermalNames.min_op_bound_col,
        ThermalNames.ramp_up_col,
        ThermalNames.ramp_down_col,
    )
    @classmethod
    def dtype_str_int_float_none(cls, series: Series[Any]) -> Series[bool]:
        """Check if values in the series are of datatype: str, int, float or None."""
        return dtype_str_int_float_none(series)

    @pa.check(
        ThermalNames.capacity_col,
        ThermalNames.full_load_col,
        ThermalNames.part_load_col,
        ThermalNames.voc_col,
        ThermalNames.emission_coeff_col,
    )
    @classmethod
    def numeric_values_greater_than_or_equal_to_0(cls, series: Series[Any]) -> Series[bool]:
        """Check if numeric values in the series are greater than or equal to zero."""
        return numeric_values_greater_than_or_equal_to(series, 0)


class ThermalMetadataSchema(_AttributeMetadataSchema):
    """Pandera DataFrameModel schema for metadata in the Thermal.Generators file."""

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
        return check_unit_is_str_for_attributes(
            df,
            [
                ThermalNames.emission_coeff_col,
                ThermalNames.capacity_col,
                ThermalNames.voc_col,
                ThermalNames.start_costs_col,
                # ThermalNames.ramp_up_col, # ?
                # ThermalNames.ramp_down_col, # ?
            ],
        )
