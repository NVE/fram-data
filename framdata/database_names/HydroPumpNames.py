"""
Define the PumpNames class and related Pandera schemas for handling hydropower pump data.

Includes attribute and metadata validation for the Hydropower.Pumps file.
"""

from typing import ClassVar

import pandas as pd
import pandera as pa
from framcore.attributes import Conversion, HydroPump, MaxFlowVolume
from framcore.metadata import Meta
from numpy.typing import NDArray

from framdata.database_names._attribute_metadata_names import _AttributeMetadataSchema
from framdata.database_names._base_names import _BaseComponentsNames


class HydroPumpNames(_BaseComponentsNames):
    """Handle naming conventions, schema definitions, and component creation for hydropower pump data."""

    id_col = "PumpID"
    node_col = "PowerNode"
    pump_from_col = "PumpFrom"
    pump_to_col = "PumpTo"
    power_capacity_col = "PowerCapacity"
    vol_capacity_col = "Capacity"
    energy_equiv_col = "EnergyEq"
    h_min_col = "HeadMin"
    h_max_col = "HeadMax"
    q_min_col = "QMin"
    q_max_col = "QMax"

    columns: ClassVar[list[str]] = [
        id_col,
        node_col,
        pump_from_col,
        pump_to_col,
        power_capacity_col,
        vol_capacity_col,
        energy_equiv_col,
        h_min_col,
        h_max_col,
        q_min_col,
        q_max_col,
    ]

    ref_columns: ClassVar[list[str]] = [
        node_col,
        pump_from_col,
        pump_to_col,
        power_capacity_col,
        vol_capacity_col,
        energy_equiv_col,
        h_min_col,
        h_max_col,
        q_min_col,
        q_max_col,
    ]

    @staticmethod
    def create_component(
        row: NDArray,
        indices: dict[str, int],
        meta_columns: set[str],
        meta_data: pd.DataFrame,
        attribute_objects: dict[str, tuple[object, dict[str, Meta]]] | None = None,
    ) -> dict[str, HydroPump]:
        """
        Create a HydroPump object from a row in the Hydropower.Pumps table.

        Args:
            row (NDArray): Array containing the values of one table row, represeting one HydroModule object.
            indices (list[str, int]): Mapping of table's Column names to the array's indices.
            meta_columns (set[str]): Set of columns used to tag object with memberships.
            meta_data (pd.DataFrame): Dictionary containing at least unit of every column.
            attribute_objects (dict[str, tuple[object, dict[str, Meta]]], optional): NOT USED, currently only used in HydroModulesNames.

        Returns:
            dict[str, HydroPump]: A dictionary with the pump ID as key and the module unit as value.

        """
        columns_to_parse = [
            HydroPumpNames.power_capacity_col,
            HydroPumpNames.vol_capacity_col,
            HydroPumpNames.energy_equiv_col,
            HydroPumpNames.h_min_col,
            HydroPumpNames.h_max_col,
            HydroPumpNames.q_min_col,
            HydroPumpNames.q_max_col,
        ]

        arg_user_code = HydroPumpNames._parse_args(row, indices, columns_to_parse, meta_data)

        pump = HydroPump(
            power_node=row[indices[HydroPumpNames.node_col]],
            from_module=row[indices[HydroPumpNames.pump_from_col]],
            to_module=row[indices[HydroPumpNames.pump_to_col]],
            water_capacity=MaxFlowVolume(level=arg_user_code[HydroPumpNames.vol_capacity_col]),
            energy_equivalent=Conversion(level=arg_user_code[HydroPumpNames.energy_equiv_col]),
            power_capacity=MaxFlowVolume(level=arg_user_code[HydroPumpNames.power_capacity_col]),
            head_max=arg_user_code[HydroPumpNames.h_max_col],
            head_min=arg_user_code[HydroPumpNames.h_min_col],
            q_max=arg_user_code[HydroPumpNames.q_max_col],
            q_min=arg_user_code[HydroPumpNames.q_min_col],
        )

        meta = {}
        HydroPumpNames._add_meta(meta, row, indices, meta_columns)

        return {row[indices[HydroPumpNames.id_col]]: (pump, meta)}

    @staticmethod
    def get_attribute_data_schema() -> pa.DataFrameModel:
        """
        Get the Pandera DataFrameModel schema for attribute data in the Hydropower.Pumps file.

        Returns:
            pa.DataFrameModel: Pandera DataFrameModel schema for the Pump attribute data.

        """
        return PumpSchema

    @staticmethod
    def get_metadata_schema() -> pa.DataFrameModel:
        """
        Get the Pandera DataFrameModel schema for the metadata table in the Hydropower.Pumps file.

        Returns:
            pa.DataFrameModel: Pandera DataFrameModel schema for the Pump metadata.

        """
        return PumpMetadataSchema

    @staticmethod
    def _get_unique_check_descriptions() -> dict[str, tuple[str, bool]]:
        """
        Retrieve a dictionary with descriptons of validation checks that are specific to the Pump schemas.

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
        Format the error DataFrame according to the validation checks that are specific to the Pump schemas.

        Args:
            errors (pd.DataFrame): The error DataFrame containing validation errors.

        Returns:
            pd.DataFrame: The updated error DataFrame with formatted rows for unique validation checks.

        """
        return None


class PumpSchema(pa.DataFrameModel):
    """Pandera DataFrameModel schema for attribute data in the Hydropower.Pumps file."""

    pass


class PumpMetadataSchema(_AttributeMetadataSchema):
    """Pandera DataFrameModel schema for metadata in the Hydropower.Pumps file."""

    pass
