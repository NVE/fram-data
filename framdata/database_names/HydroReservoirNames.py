"""
Module for handling reservoir names and schemas in hydropower data.

This module defines the ReservoirNames class for managing reservoir attributes,
and provides Pandera schemas for validating reservoir attribute and metadata tables.
"""

from typing import ClassVar

import pandas as pd
import pandera as pa
from framcore.attributes import HydroReservoir, ReservoirCurve, StockVolume
from framcore.metadata import Meta
from numpy.typing import NDArray

from framdata.database_names._attribute_metadata_names import _AttributeMetadataSchema
from framdata.database_names._base_names import _BaseComponentsNames


class HydroReservoirNames(_BaseComponentsNames):
    """
    Class for managing reservoir attribute names and providing methods for schema validation and component creation.

    This class defines column names for reservoir attributes, methods for creating HydroReservoir components,
    and functions to retrieve Pandera schemas for validating reservoir attribute and metadata tables.
    """

    id_col = "ReservoirID"
    capacity_col = "Capacity"
    res_curve_col = "ReservoirCurve"
    min_res_col = "MinOperationalFilling"
    min_penalty_col = "MinViolationPenalty"
    max_res_col = "MaxOperationalFilling"
    max_penalty_col = "MaxViolationPenalty"
    res_buf_col = "TargetFilling"
    buf_penalty_col = "TargetViolationPenalty"

    columns: ClassVar[list[str]] = [
        id_col,
        capacity_col,
        res_curve_col,
        min_res_col,
        max_res_col,
        res_buf_col,
        min_penalty_col,
        max_penalty_col,
        buf_penalty_col,
    ]

    ref_columns: ClassVar[list[str]] = [
        capacity_col,
        res_curve_col,
        min_res_col,
        max_res_col,
        res_buf_col,
        min_penalty_col,
        max_penalty_col,
        buf_penalty_col,
    ]

    @staticmethod
    def create_component(
        row: NDArray,
        indices: dict[str, int],
        meta_columns: set[str],
        meta_data: pd.DataFrame,
        attribute_objects: dict[str, tuple[object, dict[str, Meta]]] | None = None,
    ) -> dict[str, HydroReservoir]:
        """
        Create a HydroReservoir object.

        Args:
            row (NDArray): Array containing the values of one table row, represeting one HydroModule object.
            indices (list[str, int]): Mapping of table's Column names to the array's indices.
            meta_columns (set[str]): Set of columns used to tag object with memberships.
            meta_data (pd.DataFrame): Dictionary containing at least unit of every column.
            attribute_objects (dict[str, tuple[object, dict[str, Meta]]], optional): NOT USED, currently only used in HydroModulesNames.

        Returns:
            dict[str, HydroReservoir]: A dictionary with the inflow ID as key and the module unit as value.

        """
        columns_to_parse = [
            HydroReservoirNames.capacity_col,
            HydroReservoirNames.res_curve_col,
            HydroReservoirNames.min_res_col,
            HydroReservoirNames.max_res_col,
            HydroReservoirNames.res_buf_col,
            HydroReservoirNames.min_penalty_col,
            HydroReservoirNames.max_penalty_col,
            HydroReservoirNames.buf_penalty_col,
        ]

        arg_user_code = HydroReservoirNames._parse_args(row, indices, columns_to_parse, meta_data)

        reservoir_curve = ReservoirCurve(arg_user_code[HydroReservoirNames.res_curve_col])

        reservoir = HydroReservoir(
            capacity=StockVolume(level=arg_user_code[HydroReservoirNames.capacity_col]),
            reservoir_curve=reservoir_curve,
        )

        meta = {}
        HydroReservoirNames._add_meta(meta, row, indices, meta_columns)

        return {row[indices[HydroReservoirNames.id_col]]: (reservoir, meta)}

    @staticmethod
    def get_attribute_data_schema() -> pa.DataFrameModel:
        """
        Get the Pandera DataFrameModel schema for attribute data in the Hydropower.Reservoirs file.

        Returns:
            pa.DataFrameModel: Pandera DataFrameModel schema for the Reservoir attribute data.

        """
        return HydroReservoirSchema

    @staticmethod
    def get_metadata_schema() -> pa.DataFrameModel:
        """
        Get the Pandera DataFrameModel schema for the metadata table in the Hydropower.Reservoirs file.

        Returns:
            pa.DataFrameModel: Pandera DataFrameModel schema for the Reservoir metadata.

        """
        return HydroReservoirMetadataSchema

    @staticmethod
    def _get_unique_check_descriptions() -> dict[str, tuple[str, bool]]:
        """
        Retrieve a dictionary with descriptons of validation checks that are specific to the Reservoir schemas.

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
        Format the error DataFrame according to the validation checks that are specific to the Reservoir schemas.

        Args:
            errors (pd.DataFrame): The error DataFrame containing validation errors.

        Returns:
            pd.DataFrame: The updated error DataFrame with formatted rows for unique validation checks.

        """
        return None


class HydroReservoirSchema(pa.DataFrameModel):
    """Pandera DataFrameModel schema for attribute data in the Hydropower.Reservoirs file."""

    pass


class HydroReservoirMetadataSchema(_AttributeMetadataSchema):
    """Pandera DataFrameModel schema for metadata in the Hydropower.Reservoirs file."""

    pass
