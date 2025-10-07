"""Interface for database names classes which create Components."""

from abc import ABC, abstractmethod
from typing import ClassVar

import pandas as pd
import pandera as pa
from framcore import Base
from framcore.components import Component
from framcore.expressions import Expr
from framcore.metadata import Member, Meta
from framcore.timevectors import ConstantTimeVector, ReferencePeriod
from numpy.typing import NDArray

from framdata.database_names._attribute_metadata_names import _AttributeMetadataNames as Amn
from framdata.database_names.validation_functions import STANDARD_CHECK_DESCRIPTION


def _conflict_meta_msg(id1: str, id2: str, key: str, v1: object, v2: object) -> str:
    return f"Conflicting metadata in {id1} and attribute {id2}: metadata key {key} exists in both with different values. Values: {v1} and {v2}"


class _BaseComponentsNames(Base, ABC):
    """Abstact base class with some helper functions for Components Names."""

    # The following class attributes must be defined in subclasses.
    columns: ClassVar[list[str]]  # All columns in the table.
    ref_columns: ClassVar[list[str]]  # Columns that are references to ids in other files.

    # Column names in Pandera's error/failure cases dataframe
    COL_SCHEMA = "schema_context"
    COL_COLUMN = "column"
    COL_CHECK = "check"
    COL_CHECK_NUMBER = "check_number"
    COL_FAILURE_CASE = "failure_case"
    COL_IDX = "index"
    COL_CHECK_DESC = "check_description"
    COL_WARNING = "is_warning"

    @staticmethod
    @abstractmethod
    def create_component(
        row: NDArray,
        indices: dict[str, int],
        meta_columns: set[str],
        meta_data: pd.DataFrame,
        attribute_objects: dict[str, tuple[object, dict[str, Meta]]] | None = None,
    ) -> dict[str, None | Component | tuple[object, dict[str, Meta]]]:
        """
        Interface for static method which creates a Component from a table row.

        Args:
            row (NDArray): Array containing the values of one table row, representing one Component.
            indices (list[str, int]): Mapping of table's Column names to the array's indices.
            meta_columns (list[str]): Set of columns which defines memberships in meta groups for aggregation.
            meta_data (pd.DataFrame): Dictionary containing at least unit of every column.
            attribute_objects (dict[str, tuple[object, dict[str, Meta]]] | None): Dictionary of objects which are part of the main one returned by
                                                                              this function.

        Returns:
            dict[str, Component | tuple[object, dict[str, Meta]]]: Dictionary with an ID as key and a Component as value.
                                                                   List of the Component's references to other objects' IDs.

        """
        pass

    @staticmethod
    def _add_meta(container: Component | dict, row: NDArray, indices: dict[str, int], meta_columns: list[str], unit: str | None = None) -> None:
        """
        Add metadata to the Component or dictionary object.

        Args:
            container (Component | dict): Container object for the metadata.
            row (NDArray): Array containing the values of one table row.
            indices (dict[str, int]): Mapping of table's Column names to the row array's indices.
            meta_columns (list[str]): Names of meta columns defining memberships/groups.
            unit (str | None): Unit of the values in the row.

        """
        for meta_key in meta_columns:
            row_value = row[indices[meta_key]]
            meta_value = row_value
            if meta_value is None:
                continue

            meta_value = Member(row_value)

            if isinstance(container, Component):
                container.add_meta(meta_key, meta_value)
            else:
                container[meta_key] = meta_value

    @staticmethod
    def _merge_attribute_meta(parent_name: str, parent: Component, attribute_meta: dict[str, dict[str, Meta]]) -> None:
        errors = list()
        parent_keys = parent.get_meta_keys()

        compared = set()
        # validate meta
        merged_meta = {}

        for attr_name, meta in attribute_meta.items():
            compare_attrs = {k for k in attribute_meta if k not in compared}
            for comp_attr in compare_attrs:
                comp_meta = attribute_meta[comp_attr]
                errors += [_conflict_meta_msg(attr_name, comp_attr, k, v, comp_meta[k]) for k, v in meta.items() if k in comp_meta and v != comp_meta[k]]
            conflict_parent = {
                _conflict_meta_msg(parent_name, attr_name, key, parent.get_meta(key), v)
                for key, v in meta.items()
                if key in parent_keys and parent.get_meta(key) != v
            }

            errors += conflict_parent
            compared.add(attr_name)
            merged_meta.update(meta)

        if errors:
            errors_str = "\n".join(errors)
            message = f"Found errors with metadata connected to attributes of component {parent} with ID {parent_name}:\n{errors_str}"
            raise RuntimeError(message)

        for k, m in merged_meta.items():
            parent.add_meta(k, m)

    @staticmethod
    def _ref_period_lacks_profiles(
        row: NDArray,
        indices: dict[str, int],
        profile_columns: list[str],
        meta_data: dict[str, str | Expr | None],
    ) -> dict[str, str | None]:
        return all([row[indices[c]] is None for c in profile_columns])

    @staticmethod
    def _parse_args(
        row: NDArray,
        indices: dict[str, int],
        columns_to_parse: list[str],
        meta_data: dict[str, str | Expr | None],
    ) -> dict[str, str | None]:
        """
        Parse values in dictionary to usercode or None.

        Args:
            row (NDArray): Array containing the values of one table row.
            indices (dict[str, int]): Mapping of table's Column names to the row array's indices.
            columns_to_parse (list[str]): List of column names to parse.
            meta_data (dict[str, str | None]): Dictionary containing file metadata with unit of the columns.

        Returns:
            dict[str, str|None]: Mapping of column name as key and user code version of the row value.

        """
        parsed_args = {}
        for col_name in columns_to_parse:
            arg = row[indices[col_name]]
            value = _BaseComponentsNames._parse_float_or_str(arg)
            if isinstance(value, float):
                unit = Amn.get_meta(meta_data, Amn.unit, col_name)
                is_max_level = Amn.get_meta(meta_data, Amn.is_max_level, col_name)
                is_zero_one_profile = Amn.get_meta(meta_data, Amn.is_zero_one_profile, col_name)
                start_year = Amn.get_meta(meta_data, Amn.start_year, col_name)
                num_years = Amn.get_meta(meta_data, Amn.num_years, col_name)
                ref_period = None
                if start_year and num_years:
                    ref_period = ReferencePeriod(int(start_year), int(num_years))

                parsed_value = ConstantTimeVector(
                    value,
                    unit,
                    _BaseComponentsNames._parse_bool(is_max_level),
                    _BaseComponentsNames._parse_bool(is_zero_one_profile),
                    ref_period,
                )
            else:
                parsed_value = value
            parsed_args[col_name] = parsed_value
        return parsed_args

    @staticmethod
    def _parse_float_or_str(value: float | int | str | None) -> str | float | None:
        """
        Convert the input value to a float if possible, otherwise return it as a string.

        Args:
            value (Union[float, int, str]): The value to be converted.

        Returns:
            str|float: The converted value as a float if possible, otherwise as a string.

        """
        if value is None:
            return value
        try:
            value = float(value)
        except ValueError:
            value = str(value)
        return value

    @staticmethod
    def _parse_bool(value: bool | None) -> bool | None:
        if value is None:
            return value
        try:
            return bool(value)
        except ValueError as e:
            message = f"Could not convert value {value} to boolean."
            raise ValueError(message) from e

    @classmethod
    def validate(cls, schema: pa.DataFrameModel, data: pd.DataFrame) -> pd.DataFrame | None:
        """
        Validate a table in the NVE database according to its Pandera DataFrameModel schema.

        Args:
            schema (pa.DataFrameModel): The Pandera schema to validate the DataFrame against.
            data (pd.DataFrame): The DataFrame to validate.

        Returns:
            None: If the DataFrame is valid.
            pd.DataFrame: DataFrame containing details of validation errors if the DataFrame is invalid.

        """
        try:
            schema.validate(data, lazy=True)
        except pa.errors.SchemaErrors as e:
            errors = e.failure_cases
            return cls._format_error_dataframe(errors)

    @staticmethod
    def _get_attribute_object(
        attribute_objects: dict[str, tuple[object, dict[str, Meta]] | None],
        attribute_id: str | None,
        parent_id: str,
        parent_class: Component,
        expected_class: object,
    ) -> tuple[object | None, dict[str, Meta] | None]:
        if attribute_id is None:
            return None, None
        try:
            if attribute_objects[attribute_id] is None:
                return None, None
            attribute, meta = attribute_objects[attribute_id]

        except KeyError as e:
            message = (
                f"{parent_class} with ID {parent_id} refers to an attribute object of type {expected_class} with id "
                f"{attribute_id}. The attribute was not found in the available data. Please make sure all attribute "
                "objects are populated before their parent components."
            )
            raise KeyError(message) from e
        else:
            if not isinstance(attribute, expected_class | type(None)):
                message = f"{parent_class} with ID {parent_id} expected class {expected_class} for attribute with id {attribute_id}. Got {type(attribute)}."
                raise ValueError(message)
            return attribute, meta

    @staticmethod
    @abstractmethod
    def get_attribute_data_schema() -> pa.DataFrameModel:
        """
        Get the Pandera DataFrameModel schema for an attribute data table in the NVE database.

        Returns:
            pa.DataFrameModel: Pandera DataFrameModel schema for attribute data.

        """
        pass

    @staticmethod
    @abstractmethod
    def get_metadata_schema() -> pa.DataFrameModel:
        """
        Get the Pandera DataFrameModel schema for a metadata table in the NVE database.

        Returns:
            pa.DataFrameModel: Pandera DataFrameModel schema for metadata.

        """
        pass

    @staticmethod
    def get_references(row: NDArray, indices: dict[str, int], ref_columns: list[str]) -> set[str]:
        """
        Get references to other data objects' IDs.

        Args:
            row (NDArray): Array containing the values of one table row.
            indices (dict[str, int]): Mapping of table's Column names to the row array's indices.
            ref_columns (list[str]): List of column names that are references to other components.

        Returns:
            list[str]: List of references to other components.

        """
        return {row[indices[c]] for c in ref_columns if isinstance(row[indices[c]], str)}  # assume strings are IDs

    @classmethod
    def _format_error_dataframe(
        cls,
        errors: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Add descriptions of validation checks and format the error DataFrame for better user-readability.

        This method enhances the error DataFrame by adding user-friendly descriptions of validation checks,
        ensuring the structure is consistent and organized. It handles formatting of common validation checks
        shared by most subclasses and incorporates any unique check descriptions specific to the subclass.

        Args:
            errors (pd.DataFrame): DataFrame containing validation errors. Pandera's standard error reports DataFrame.

        Returns:
            pd.DataFrame: A formatted and organized DataFrame with user-friendly check descriptions.

        """
        check_desriptions = cls._get_check_descriptions()
        errors = errors.merge(check_desriptions, how="left", on=cls.COL_CHECK)

        errors[cls.COL_IDX] = errors[cls.COL_IDX] + 2
        errors = errors.drop(columns=[cls.COL_SCHEMA, cls.COL_CHECK_NUMBER], errors="ignore")

        errors_formatted = cls._format_unique_checks(errors)
        if errors_formatted is not None:
            errors = errors_formatted

        errors = cls._format_unit_check(errors, "check_unit_is_str_for_attributes")

        errors = cls._format_field_uniqueness_check(errors)

        errors = errors.sort_values(by=cls.COL_WARNING, ascending=True)
        errors = errors[[cls.COL_COLUMN, cls.COL_CHECK, cls.COL_CHECK_DESC, cls.COL_FAILURE_CASE, cls.COL_IDX, cls.COL_WARNING]]
        return errors.reset_index(drop=True)

    @staticmethod
    def _format_field_uniqueness_check(
        errors: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Format the error DataFrame for field uniqueness checks.

        This method processes validation errors that come from the built-in field uniqueness check. It groups the errors
        by column and failure case, ensuring that duplicate entries are consolidated into a single row with a list of
        index values.

        Args:
            errors (pd.DataFrame): DataFrame containing validation errors.

        Returns:
            pd.DataFrame: The updated error DataFrame with formatted rows for field uniqueness checks.

        """
        if "field_uniqueness" in errors[_BaseComponentsNames.COL_CHECK].to_numpy():
            duplicates = errors[errors[_BaseComponentsNames.COL_CHECK] == "field_uniqueness"]
            if len(duplicates) > 1:
                grouped_duplicates = duplicates.groupby(
                    [_BaseComponentsNames.COL_COLUMN, _BaseComponentsNames.COL_FAILURE_CASE],
                    as_index=False,
                ).agg(
                    {
                        _BaseComponentsNames.COL_IDX: list,
                        _BaseComponentsNames.COL_CHECK: "first",
                        _BaseComponentsNames.COL_CHECK_DESC: "first",
                        _BaseComponentsNames.COL_WARNING: "first",
                    },
                )
                errors = errors[~(errors[_BaseComponentsNames.COL_CHECK] == "field_uniqueness")]
                errors = pd.concat([errors, grouped_duplicates])
        return errors

    @staticmethod
    def _format_unit_check(errors: pd.DataFrame, check_name: str = "check_unit_is_str_for_attributes") -> pd.DataFrame:
        """
        Format the error DataFrame for a dataframe-level check that validates the "unit" column in metadata tables.

        This method processes validation errors that come from a dataframe-level check on the "unit" column in metadata
        tables. The default reporting on failed dataframe-level checks in Pandera's standard error reports DataFrame
        (errors) is not very user-friendly. It can contain uneccassary rows about columns that are not relevant to the
        check and will not include rows about the "unit" column if those columns have missing values. This method
        removes uneccassary rows from the error dataframe and ensures that rows with information about the "unit" column
        are included.

        Args:
            errors (pd.DataFrame): DataFrame containing validation errors.
            check_name (str): The name of the check to format. Defaults to "check_unit_is_str_for_attributes",
            which is a common validation check used to ensure that the "unit" column contains string values for
            specific attributes in metadata tables. Subclasses may override this default to format their own version of
            a dataframe-level check on the "unit" column.

        Returns:
            pd.DataFrame: The updated error DataFrame with formatted rows for the specified validation check.

        """
        if check_name in errors[_BaseComponentsNames.COL_CHECK].to_numpy():
            check_rows = errors.loc[errors[_BaseComponentsNames.COL_CHECK] == check_name]
            errors = errors[~(errors[_BaseComponentsNames.COL_CHECK] == check_name)]
            check_description_str = check_rows[_BaseComponentsNames.COL_CHECK_DESC].unique()[0]
            check_unit_rows = []
            for idx in check_rows[_BaseComponentsNames.COL_IDX].unique():
                error_case = check_rows[check_rows[_BaseComponentsNames.COL_IDX] == idx]
                try:
                    error_row = error_case[error_case[_BaseComponentsNames.COL_COLUMN] == Amn.unit].iloc[0]
                    error_row = error_row.tolist()
                except IndexError:
                    error_row = [
                        Amn.unit,
                        check_name,
                        None,
                        idx,
                        check_description_str,
                        False,
                    ]
                check_unit_rows.append(error_row)

            errors = pd.concat([errors, pd.DataFrame(check_unit_rows, columns=errors.columns)], ignore_index=True)
        return errors

    @classmethod
    def _get_check_descriptions(cls) -> pd.DataFrame:
        """
        Get a DataFrame with descriptions for Pandera validation checks.

        This method combines standard check descriptions with unique check descriptions (if provided by the subclass)
        and returns a DataFrame containing details about the checks. The unique check descriptions will override the
        standard check descriptions, if they have the same key.

        Returns:
            pd.DataFrame: A DataFrame with the following columns:
                - COL_CHECK: The name of the check (e.g., "dtype('str')", "field_uniqueness").
                - COL_CHECK_DESC: A description of the check (e.g., "Expected value to be of type str.").
                - COL_WARNING: A boolean indicating whether the check is a warning (True) or an error (False).

        """
        standard_check_descriptions = STANDARD_CHECK_DESCRIPTION
        unique_check_descriptions = cls._get_unique_check_descriptions()
        if unique_check_descriptions is not None:
            standard_check_descriptions.update(unique_check_descriptions)
        return pd.DataFrame(
            [(key, value[0], value[1] if len(value) > 1 else False) for key, value in STANDARD_CHECK_DESCRIPTION.items()],
            columns=[cls.COL_CHECK, cls.COL_CHECK_DESC, cls.COL_WARNING],
        )

    @staticmethod
    @abstractmethod
    def _get_unique_check_descriptions() -> dict[str, tuple[str, bool]] | None:
        """
        Retrieve a dictionary containing descriptions for unique checks implemented in the schemas of a subclass.

        The dictionary must adhere to the following structure:
            - Key (str): The name of the validation check method. The name must be unique and match the name of a check
                         method used in a schema of the subclass.
            - Values (tuple[str, bool]):
                - The first element (str) provides a concise and user-friendly description of the check. E.g. what
                  caused the validation error or what is required for the check to pass.
                - The second element (bool) indicates whether the check is a warning (True) or an error (False).

        This method allows subclasses to define additional checks specific to their schemas, complementing or overriding
        the standard check descriptions provided by the base class.

        Returns:
            dict[str, tuple[str, bool]] | None: A dictionary containing unique check descriptions, or None if no unique
            checks are defined.

        """
        pass

    @staticmethod
    @abstractmethod
    def _format_unique_checks(errors: pd.DataFrame) -> pd.DataFrame | None:
        """
        Format the error DataFrame according to the unique check descriptions of the sub-class.

        Importantly, this method should not alter the structure of the incoming DataFrame. E.g. it should not add or
        remove columns, nor should it alter the existing column names or types.

        Args:
            errors (pd.DataFrame): The error DataFrame to be formatted.

        Returns:
            pd.DataFrame | None: A formatted DataFrame with the same structure as the input, or None if no formatting is
            required.

        Notes:
            - The structure of the incoming DataFrame includes the following columns:
                - COL_COLUMN: The name of the column where the error occurred.
                - COL_CHECK: The name of the check that failed.
                - COL_FAILURE_CASE: Details about the failure case.
                - COL_IDX: The index or indices of the rows where the error occurred.
                - COL_CHECK_DESC: A description of the failed check.
                - COL_WARNING: A boolean indicating whether the error is a warning (True) or a critical error (False).

        """
        pass
