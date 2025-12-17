"""
Defines schema, names, and component creation logic for hydropower modules.

This module provides:
- HydroModulesNames: class for column names and component creation for hydropower modules.
- HydroModuleSchema: Pandera schema for attribute data.
- HydroModuleMetadataSchema: Pandera schema for metadata.
"""

from typing import ClassVar

import pandas as pd
import pandera as pa
from framcore.attributes import AvgFlowVolume, HydroBypass, HydroGenerator, HydroPump, HydroReservoir, MaxFlowVolume
from framcore.components import Component, HydroModule
from framcore.metadata import Meta
from numpy.typing import NDArray

from framdata.database_names._attribute_metadata_names import _AttributeMetadataSchema
from framdata.database_names._base_names import _BaseComponentsNames


class HydroModulesNames(_BaseComponentsNames):
    """
    Provides column names, schema accessors, and component creation logic for hydropower modules.

    This class defines constants for column names, methods for creating HydroModule components from data rows,
    and accessors for Pandera schemas used for validation of attribute and metadata tables.
    """

    filename = "Hydropower.Modules"

    id_col = "ModuleID"
    pump_col = "Pump"
    gen_col = "Generator"
    res_col = "Reservoir"
    byp_col = "Bypass"
    hyd_code_col = "HydraulicCoupling"
    inflow_col = "Inflow"
    rel_to_col = "ReleaseTo"
    spill_to_col = "SpillTo"
    rel_cap_col = "CapacityRelease"
    min_bnd_col = "MinOperationalRelease"
    max_bnd_col = "MaxOperationalRelease"
    min_penalty_col = "MinViolationPenalty"
    max_penalty_col = "MaxViolationPenalty"

    columns: ClassVar[list[str]] = [
        id_col,
        pump_col,
        gen_col,
        res_col,
        byp_col,
        hyd_code_col,
        inflow_col,
        rel_to_col,
        spill_to_col,
        rel_cap_col,
        min_bnd_col,
        max_bnd_col,
        min_penalty_col,
        max_penalty_col,
    ]

    ref_columns: ClassVar[list[str]] = [
        rel_to_col,
        spill_to_col,
        rel_cap_col,
        min_bnd_col,
        max_bnd_col,
        min_penalty_col,
        max_penalty_col,
    ]

    @staticmethod
    def create_component(
        row: NDArray,
        indices: dict[str, int],
        meta_columns: set[str],
        meta_data: pd.DataFrame,
        attribute_objects: dict[str, tuple[object, dict[str, Meta]]] | None = None,
    ) -> dict[str, Component]:
        """
        Create a hydro module component.

        Args:
            row (NDArray): Array containing the values of one table row, represeting one HydroModule object.
            indices (list[str, int]): Mapping of table's Column names to the array's indices.
            meta_columns (set[str]): Set of columns used to tag object with memberships.
            meta_data (pd.DataFrame): Dictionary containing at least unit of every column.
            attribute_objects (dict[str, tuple[object, dict[str, Meta]]], optional): Dictionary of attributes to link to the HydroModule.

        Returns:
            dict[str, Component]: A dictionary with the module_id as key and the module unit as value.

        """
        columns_to_parse = [
            HydroModulesNames.rel_cap_col,
            HydroModulesNames.min_bnd_col,
            HydroModulesNames.max_bnd_col,
            HydroModulesNames.min_penalty_col,
            HydroModulesNames.max_penalty_col,
        ]
        name = row[indices[HydroModulesNames.id_col]]
        inflow_name = indices[HydroModulesNames.inflow_col]
        pump_name = indices[HydroModulesNames.pump_col]
        gen_name = indices[HydroModulesNames.gen_col]
        res_name = indices[HydroModulesNames.res_col]
        byp_name = indices[HydroModulesNames.byp_col]
        arg_user_code = HydroModulesNames._parse_args(row, indices, columns_to_parse, meta_data)
        inflow, inflow_meta = HydroModulesNames._get_attribute_object(
            attribute_objects,
            row[inflow_name],
            name,
            HydroModule,
            AvgFlowVolume,
        )
        pump, pump_meta = HydroModulesNames._get_attribute_object(
            attribute_objects,
            row[pump_name],
            name,
            HydroModule,
            HydroPump,
        )
        generator, generator_meta = HydroModulesNames._get_attribute_object(
            attribute_objects,
            row[gen_name],
            name,
            HydroModule,
            HydroGenerator,
        )
        reservoir, reservoir_meta = HydroModulesNames._get_attribute_object(
            attribute_objects,
            row[res_name],
            name,
            HydroModule,
            HydroReservoir,
        )
        bypass, bypass_meta = HydroModulesNames._get_attribute_object(
            attribute_objects,
            row[byp_name],
            name,
            HydroModule,
            HydroBypass,
        )
        module = HydroModule(
            release_capacity=MaxFlowVolume(level=arg_user_code[HydroModulesNames.rel_cap_col]),
            hydraulic_coupling=row[indices[HydroModulesNames.hyd_code_col]],
            inflow=inflow,
            pump=pump,
            generator=generator,
            reservoir=reservoir,
            bypass=bypass,
            release_to=row[indices[HydroModulesNames.rel_to_col]],
            spill_to=row[indices[HydroModulesNames.spill_to_col]],
        )

        if "EnergyEqDownstream" in meta_columns:
            HydroModulesNames._add_meta(module, row, indices, ["EnergyEqDownstream"], unit="kWh/m3")

        meta_columns = [c for c in meta_columns if c != "EnergyEqDownstream"]
        HydroModulesNames._add_meta(module, row, indices, meta_columns)  # fails because Modules want floats in Meta.

        attr_meta = {
            inflow_name: inflow_meta,
            pump_name: pump_meta,
            gen_name: generator_meta,
            res_name: reservoir_meta,
            byp_name: bypass_meta,
        }
        HydroModulesNames._merge_attribute_meta(
            name,
            module,
            {k: v for k, v in attr_meta.items() if k and v},
        )

        return {name: module}

    @staticmethod
    def get_attribute_data_schema() -> pa.DataFrameModel:
        """
        Get the Pandera DataFrameModel schema for attribute data in the Hydropower.Modules file.

        Returns:
            pa.DataFrameModel: Pandera DataFrameModel schema for the HydroModule attribute data.

        """
        return HydroModuleSchema

    @staticmethod
    def get_metadata_schema() -> pa.DataFrameModel:
        """
        Get the Pandera DataFrameModel schema for the metadata table in the Hydropower.Modules file.

        Returns:
            pa.DataFrameModel: Pandera DataFrameModel schema for the HydroModule metadata.

        """
        return HydroModuleMetadataSchema

    @staticmethod
    def _get_unique_check_descriptions() -> dict[str, tuple[str, bool]]:
        """
        Retrieve a dictionary with descriptons of validation checks that are specific to the HydroModule schemas.

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
        Format the error DataFrame according to the validation checks that are specific to the HydroModule schemas.

        Args:
            errors (pd.DataFrame): The error DataFrame containing validation errors.

        Returns:
            pd.DataFrame: The updated error DataFrame with formatted rows for unique validation checks.

        """
        return None


class HydroModuleSchema(pa.DataFrameModel):
    """Pandera DataFrameModel schema for attribute data in the Hydropower.Modules file."""

    pass


class HydroModuleMetadataSchema(_AttributeMetadataSchema):
    """Pandera DataFrameModel schema for metadata in the Hydropower.Modules file."""

    pass
