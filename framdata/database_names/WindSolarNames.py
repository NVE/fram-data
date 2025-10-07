"""Classes defining Wind and Solar tables and how to create Components from them."""

from typing import ClassVar

import pandas as pd
import pandera as pa
from framcore.attributes import MaxFlowVolume
from framcore.components import Solar, Wind
from framcore.metadata import Meta
from numpy.typing import NDArray

from framdata.database_names._attribute_metadata_names import _AttributeMetadataSchema
from framdata.database_names._base_names import _BaseComponentsNames


class WindSolarNames(_BaseComponentsNames):
    """Class representing the names and structure of Wind and Solar tables."""

    id_col = "ID"
    power_node_col = "PowerNode"
    profile_col = "Profile"
    type_col = "TechnologyType"
    capacity_col = "Capacity"

    columns: ClassVar[list[str]] = [
        id_col,
        power_node_col,
        profile_col,
        capacity_col,
    ]

    ref_columns: ClassVar[list[str]] = [
        power_node_col,
        profile_col,
        capacity_col,
    ]

    @staticmethod
    def get_attribute_data_schema() -> pa.DataFrameModel:
        """
        Get the Pandera DataFrameModel schema for attribute data in a Wind and Solar file.

        Returns:
            pa.DataFrameModel: Pandera DataFrameModel schema for Wind and Solar attribute data.

        """
        return WindSolarSchema

    @staticmethod
    def get_metadata_schema() -> pa.DataFrameModel:
        """
        Get the Pandera DataFrameModel schema for the metadata table in a Wind and Solar file.

        Returns:
            pa.DataFrameModel: Pandera DataFrameModel schema for the Thermal metadata.

        """
        return WindSolarMetadataSchema

    @staticmethod
    def _get_unique_check_descriptions() -> dict[str, tuple[str, bool]]:
        """
        Retrieve a dictionary with descriptons of validation checks that are specific to the Wind and Solar schemas.

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
        Format the error DataFrame according to the validation checks that are specific to the Wind and Solar schemas.

        Args:
            errors (pd.DataFrame): The error DataFrame containing validation errors.

        Returns:
            pd.DataFrame: The updated error DataFrame with formatted rows for unique validation checks.

        """
        return None


class WindSolarSchema(pa.DataFrameModel):
    """Standard Pandera DataFrameModel schema for attribute data in the Wind and Solar files."""

    pass


class WindSolarMetadataSchema(_AttributeMetadataSchema):
    """Standard Pandera DataFrameModel schema for metadata in the Wind and Solar files."""

    pass


class WindNames(WindSolarNames):
    """Class representing the names and structure of Wind tables, and method for creating Wind Component objects."""

    @staticmethod
    def create_component(
        row: NDArray,
        indices: dict[str, int],
        meta_columns: set[str],
        meta_data: pd.DataFrame,
        attribute_objects: dict[str, tuple[object, dict[str, Meta]]] | None = None,
    ) -> dict[str, Wind]:
        """
        Create a Wind Component from a row in the Wind.Generators table.

        Args:
            row (NDArray): Array containing the values of one table row, represeting one Wind object.
            indices (list[str, int]): Mapping of table's Column names to the array's indices.
            meta_columns (set[str]): Set of columns used to tag object with memberships.
            meta_data (pd.DataFrame): Dictionary containing at least unit of every column.
            attribute_objects (dict[str, tuple[object, dict[str, Meta]]] | None, optional): NOT USED

        Returns:
            dict[str, Wind]: A dictionary with the wind_id as key and the wind unit as value.

        """
        columns_to_parse = [
            WindNames.profile_col,
            WindNames.capacity_col,
        ]

        arg_user_code = WindNames._parse_args(row, indices, columns_to_parse, meta_data)

        wind = Wind(
            power_node=row[indices[WindNames.power_node_col]],
            max_capacity=MaxFlowVolume(
                level=arg_user_code[WindNames.capacity_col],
                profile=arg_user_code[WindNames.profile_col],
            ),
            voc=None,
        )
        WindNames._add_meta(wind, row, indices, meta_columns)

        return {row[indices[WindNames.id_col]]: wind}


class SolarNames(WindSolarNames):
    """Class representing the names and structure of Solar tables, and method for creating Solar Component objects."""

    @staticmethod
    def create_component(
        row: NDArray,
        indices: dict[str, int],
        meta_columns: set[str],
        meta_data: pd.DataFrame,
        attribute_objects: dict[str, tuple[object, dict[str, Meta]]] | None = None,
    ) -> dict[str, Solar]:
        """
        Create a Solar Component from a row in the Solar.Generators table.

        Args:
            row (NDArray): Array containing the values of one table row, represeting one solar object.
            indices (list[str, int]): Mapping of table's Column names to the array's indices.
            meta_columns (set[str]): Set of columns used to tag object with memberships.
            meta_data (pd.DataFrame): Dictionary containing at least unit of every column.
            attribute_objects (dict[str, tuple[object, dict[str, Meta]]] | None, optional): NOT USED

        Returns:
            dict[str, Solar]: A dictionary with the id as key and the solar unit as value.

        """
        columns_to_parse = [
            SolarNames.profile_col,
            SolarNames.capacity_col,
        ]

        arg_user_code = SolarNames._parse_args(row, indices, columns_to_parse, meta_data)

        solar = Solar(
            power_node=row[indices[SolarNames.power_node_col]],
            max_capacity=MaxFlowVolume(
                level=arg_user_code[SolarNames.capacity_col],
                profile=arg_user_code[SolarNames.profile_col],
            ),
            voc=None,
        )

        SolarNames._add_meta(solar, row, indices, meta_columns)

        return {row[indices[SolarNames.id_col]]: solar}
