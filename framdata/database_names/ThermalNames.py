"""Classes defining Thermal tables."""

from typing import ClassVar

import pandas as pd
import pandera as pa
from framcore.attributes import Conversion, Cost, Efficiency, Hours, MaxFlowVolume, Proportion, StartUpCost
from framcore.components import Thermal
from framcore.metadata import Meta
from numpy.typing import NDArray

from framdata.database_names._attribute_metadata_names import _AttributeMetadataSchema
from framdata.database_names._base_names import _BaseComponentsNames
from framdata.database_names.nodes_names import FuelNodesNames


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

    pass


class ThermalMetadataSchema(_AttributeMetadataSchema):
    """Pandera DataFrameModel schema for metadata in the Thermal.Generators file."""

    pass
