"""
Define the GeneratorNames class and related Pandera schemas for hydropower generator data.

Provides:
- GeneratorNames: class for handling generator component names and schema validation.
- GeneratorSchema: Pandera schema for generator attribute data.
- GeneratorMetadataSchema: Pandera schema for generator metadata.
"""

from typing import ClassVar

import pandas as pd
import pandera as pa
from framcore.attributes import Conversion, HydroGenerator
from framcore.metadata import Meta
from numpy.typing import NDArray

from framdata.database_names._attribute_metadata_names import _AttributeMetadataSchema
from framdata.database_names._base_names import _BaseComponentsNames


class HydroGeneratorNames(_BaseComponentsNames):
    """
    Handles generator component names and schema validation for hydropower generator data.

    Provides methods for creating generator components, retrieving Pandera schemas for attribute and metadata tables,
    and formatting validation errors specific to generator schemas.
    """

    id_col = "GeneratorID"
    node_col = "PowerNode"
    pq_curve_col = "PQCurve"
    tailw_elev_col = "TailwaterElevation"
    head_nom_col = "NominalHead"
    en_eq_col = "EnergyEq"

    columns: ClassVar[list[str]] = [
        id_col,
        node_col,
        pq_curve_col,
        tailw_elev_col,
        head_nom_col,
        en_eq_col,
    ]

    ref_columns: ClassVar[list[str]] = [
        node_col,
        pq_curve_col,
        tailw_elev_col,
        head_nom_col,
        en_eq_col,
    ]

    @staticmethod
    def create_component(
        row: NDArray,
        indices: dict[str, int],
        meta_columns: set[str],
        meta_data: pd.DataFrame,
        attribute_objects: dict[str, tuple[object, dict[str, Meta]]] | None = None,
    ) -> dict[str, tuple[HydroGenerator, dict[str, Meta]]]:
        """
        Create a hydro generator attribute object.

        Args:
            row (NDArray): Array containing the values of one table row, represeting one HydroModule object.
            indices (list[str, int]): Mapping of table's Column names to the array's indices.
            meta_columns (set[str]): Set of columns used to tag object with memberships.
            meta_data (pd.DataFrame): Dictionary containing at least unit of every column.
            attribute_objects (dict[str, tuple[object, dict[str, Meta]]], optional): NOT USED, currently only used in HydroModulesNames.

        Returns:
            dict[str, dict[str, Meta]]: A dictionary with the generator ID as key and the attribute object and metadata as value.

        """
        columns_to_parse = [
            HydroGeneratorNames.pq_curve_col,
            HydroGeneratorNames.tailw_elev_col,
            HydroGeneratorNames.head_nom_col,
            HydroGeneratorNames.en_eq_col,
        ]

        arg_user_code = HydroGeneratorNames._parse_args(row, indices, columns_to_parse, meta_data)

        generator = HydroGenerator(
            power_node=row[indices[HydroGeneratorNames.node_col]],
            energy_eq=Conversion(level=arg_user_code[HydroGeneratorNames.en_eq_col]),
            pq_curve=arg_user_code[HydroGeneratorNames.pq_curve_col],
            tailwater_elevation=arg_user_code[HydroGeneratorNames.tailw_elev_col],
            nominal_head=arg_user_code[HydroGeneratorNames.head_nom_col],
        )

        meta = {}
        HydroGeneratorNames._add_meta(meta, row, indices, meta_columns)

        return {row[indices[HydroGeneratorNames.id_col]]: (generator, meta)}

    @staticmethod
    def get_attribute_data_schema() -> pa.DataFrameModel:
        """
        Get the Pandera DataFrameModel schema for attribute data in the Hydropower.Generators file.

        Returns:
            pa.DataFrameModel: Pandera DataFrameModel schema for the Generator attribute data.

        """
        return GeneratorSchema

    @staticmethod
    def get_metadata_schema() -> pa.DataFrameModel:
        """
        Get the Pandera DataFrameModel schema for the metadata table in the Hydropower.Generators file.

        Returns:
            pa.DataFrameModel: Pandera DataFrameModel schema for the Generator metadata.

        """
        return GeneratorMetadataSchema

    @staticmethod
    def _get_unique_check_descriptions() -> dict[str, tuple[str, bool]]:
        """
        Retrieve a dictionary with descriptons of validation checks that are specific to the Generator schemas.

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
        Format the error DataFrame according to the validation checks that are specific to the Generator schemas.

        Args:
            errors (pd.DataFrame): The error DataFrame containing validation errors.

        Returns:
            pd.DataFrame: The updated error DataFrame with formatted rows for unique validation checks.

        """
        return None


class GeneratorSchema(pa.DataFrameModel):
    """Pandera DataFrameModel schema for attribute data in the Hydropower.Generators file."""

    pass


class GeneratorMetadataSchema(_AttributeMetadataSchema):
    """Pandera DataFrameModel schema for metadata in the Hydropower.Generators file."""

    pass
