"""
Contain the BypassNames class and related Pandera schemas for handling hydropower bypass data.

Includes attribute and metadata schemas.
"""

from typing import ClassVar

import pandas as pd
import pandera as pa
from framcore.attributes import HydroBypass, MaxFlowVolume
from framcore.metadata import Meta
from numpy.typing import NDArray

from framdata.database_names._attribute_metadata_names import _AttributeMetadataSchema
from framdata.database_names._base_names import _BaseComponentsNames


class HydroBypassNames(_BaseComponentsNames):
    """
    Define naming conventions and attribute object creation for HydroBypass object, which is an attribute of the HydroModule.

    Provides methods for creating generator components, retrieving Pandera schemas for attribute and metadata tables,
    and formatting validation errors specific to generator schemas.

    """

    id_col = "BypassID"
    to_col = "BypassTo"
    cap_col = "Capacity"
    min_bnd_col = "MinOperationalBypass"
    min_penalty_col = "MinViolationPenalty"

    columns: ClassVar[list[str]] = [id_col, to_col, cap_col, min_bnd_col, min_penalty_col]

    ref_columns: ClassVar[list[str]] = [to_col, cap_col, min_bnd_col, min_penalty_col]

    @staticmethod
    def create_component(
        row: NDArray,
        indices: dict[str, int],
        meta_columns: set[str],
        meta_data: pd.DataFrame,
        attribute_objects: dict[str, tuple[object, dict[str, Meta]]] | None = None,
    ) -> dict[str, HydroBypass]:
        """
        Create a HydroBypass object.

        Args:
            row (NDArray): Array containing the values of one table row, represeting one HydroModule object.
            indices (list[str, int]): Mapping of table's Column names to the array's indices.
            meta_columns (set[str]): Set of columns used to tag object with memberships.
            meta_data (pd.DataFrame): Dictionary containing at least unit of every column.
            attribute_objects (dict[str, tuple[object, dict[str, Meta]]], optional): NOT USED, currently only used in HydroModulesNames.

        Returns:
            dict[str, HydroBypass]: A dictionary with the bypass ID as key and the module unit as value.

        """
        columns_to_parse = [
            HydroBypassNames.id_col,
            HydroBypassNames.to_col,
            HydroBypassNames.cap_col,
            HydroBypassNames.min_bnd_col,
            HydroBypassNames.min_penalty_col,
        ]

        arg_user_code = HydroBypassNames._parse_args(row, indices, columns_to_parse, meta_data)

        bypass = HydroBypass(
            to_module=row[indices[HydroBypassNames.to_col]],
            # capacity=SoftFlowCapacity(
            #     level_input=arg_user_code[BypassNames.cap_col],
            #     min_profile_input=arg_user_code[BypassNames.min_bnd_col],
            #     min_penalty=arg_user_code[BypassNames.min_penalty_col],
            # ),
            capacity=MaxFlowVolume(level=arg_user_code[HydroBypassNames.cap_col]),
        )

        meta = {}
        HydroBypassNames._add_meta(meta, row, indices, meta_columns)

        return {row[indices[HydroBypassNames.id_col]]: (bypass, meta)}

    @staticmethod
    def get_attribute_data_schema() -> pa.DataFrameModel:
        """
        Get the Pandera DataFrameModel schema for attribute data in the Hydropower.Bypass file.

        Returns:
            pa.DataFrameModel: Pandera DataFrameModel schema for the Bypass attribute data.

        """
        return HydroBypassSchema

    @staticmethod
    def get_metadata_schema() -> pa.DataFrameModel:
        """
        Get the Pandera DataFrameModel schema for the metadata table in the Hydropower.Bypass file.

        Returns:
            pa.DataFrameModel: Pandera DataFrameModel schema for the Bypass metadata.

        """
        return HydroBypassMetadataSchema

    @staticmethod
    def _get_unique_check_descriptions() -> dict[str, tuple[str, bool]]:
        """
        Retrieve a dictionary with descriptons of validation checks that are specific to the Bypass schemas.

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
        Format the error DataFrame according to the validation checks that are specific to the Bypass schemas.

        Args:
            errors (pd.DataFrame): The error DataFrame containing validation errors.

        Returns:
            pd.DataFrame: The updated error DataFrame with formatted rows for unique validation checks.

        """
        return None


class HydroBypassSchema(pa.DataFrameModel):
    """Pandera DataFrameModel schema for attribute data in the Hydropower.Bypass file."""

    pass


class HydroBypassMetadataSchema(_AttributeMetadataSchema):
    """Pandera DataFrameModel schema for metadata in the Hydropower.Bypass file."""

    pass
