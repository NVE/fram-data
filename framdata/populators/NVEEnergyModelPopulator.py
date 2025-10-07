"""Contain the NVEEnergyModelPopulator class."""

from pathlib import Path
from time import time
from typing import ClassVar

import pandas as pd
from framcore.components import Component
from framcore.curves import Curve

# Core
from framcore.expressions import Expr
from framcore.metadata import Meta
from framcore.populators import Populator
from framcore.timevectors import TimeVector
from framcore.utils import set_global_energy_equivalent

from framdata.database_names._base_names import _BaseComponentsNames
from framdata.database_names.DatabaseNames import DatabaseNames as DbN
from framdata.database_names.DemandNames import DemandNames

# Data
from framdata.database_names.HydroBypassNames import HydroBypassNames
from framdata.database_names.HydroGeneratorNames import HydroGeneratorNames
from framdata.database_names.HydroInflowNames import HydroInflowNames
from framdata.database_names.HydroModulesNames import HydroModulesNames
from framdata.database_names.HydroPumpNames import HydroPumpNames
from framdata.database_names.HydroReservoirNames import HydroReservoirNames
from framdata.database_names.nodes_names import EmissionNodesNames, FuelNodesNames, PowerNodesNames
from framdata.database_names.ThermalNames import ThermalNames
from framdata.database_names.TransmissionNames import TransmissionNames
from framdata.database_names.WindSolarNames import SolarNames, WindNames
from framdata.populators._DatabaseInterpreter import _DatabaseInterpreter
from framdata.populators._DataObjectManager import _DataObjectManager
from framdata.populators.NVEPathManager import NVEPathManager


class NVEEnergyModelPopulator(Populator):
    """
    Fill a Model with objects created from an NVE database by using classes defined in framdata/database_names.

    Creates five different kinds of objects with different purposes:
        - Component: Objects containing and describing attributes of elements in the power market.
        - 'Attribute object': Contains attributes which are considered parts of a Component, but grouped together in smaller parts of the Component.
                               These objects are held within a proper Component object by composition.
        - TimeVector: Represents and describes the behavior of a single time vector and can return this vectors index, values and metadata.
        - Curve: Represents and describes behavior of curves with values along x- and y-axes. Can return the axes and metadata.
        - Loader: The Loader objects are responsible for reading of data from a single source. Each TimeVector and Curve is connected to a Loader and requests
                  data from the loader using an ID.

    """

    _COMPONENT_DICT: ClassVar[dict[str, _BaseComponentsNames]] = {
        DbN.fuel_nodes: FuelNodesNames,
        DbN.emission_nodes: EmissionNodesNames,
        DbN.power_nodes: PowerNodesNames,
        DbN.thermal_generators: ThermalNames,
        DbN.demand_consumers: DemandNames,
        DbN.wind_generators: WindNames,
        DbN.solar_generators: SolarNames,
        DbN.transmission_grid: TransmissionNames,
        DbN.hydro_modules: HydroModulesNames,
    }

    _ATTRIBUTES_DICT: ClassVar[dict[str, _BaseComponentsNames]] = {
        DbN.hydro_inflow: HydroInflowNames,
        DbN.hydro_bypass: HydroBypassNames,
        DbN.hydro_pumps: HydroPumpNames,
        DbN.hydro_generators: HydroGeneratorNames,
        DbN.hydro_reservoirs: HydroReservoirNames,
    }

    _TIME_VECTOR_LIST: ClassVar[list[tuple[str, bool]]] = [  # (vector file id, required to be whole years)
        (DbN.power_nodes_prices, False),
        (DbN.power_nodes_profiles, True),
        (DbN.fuel_nodes_prices, False),
        (DbN.fuel_nodes_profiles, True),
        (DbN.emission_nodes_prices, False),
        (DbN.emission_nodes_profiles, True),
        (DbN.thermal_generators_capacity, False),
        (DbN.thermal_generators_profiles, True),
        (DbN.demand_consumers_capacity, False),
        (DbN.demand_consumers_profiles_weatheryears, False),
        (DbN.demand_consumers_profiles_oneyear, False),
        (DbN.transmission_capacity, False),
        (DbN.transmission_loss, False),
        (DbN.transmission_profiles, True),
        (DbN.demand_consumers_normalprices, False),
        (DbN.wind_generators_capacity, False),
        (DbN.wind_generators_profiles, True),
        (DbN.solar_generators_capacity, False),
        (DbN.solar_generators_profiles, True),
        (DbN.hydro_bypass_operationalbounds_restrictions, False),
        (DbN.hydro_inflow_profiles, True),
        (DbN.hydro_modules_operationalbounds_restrictions, False),
        (DbN.hydro_reservoirs_operationalbounds_restrictions, False),
    ]

    _CURVE_LIST: ClassVar[list[str]] = [
        DbN.hydro_pqcurves,
        DbN.hydro_curves,
    ]

    _DATABASE_ID_LIST: ClassVar[list[str]] = _TIME_VECTOR_LIST + _CURVE_LIST + list(_COMPONENT_DICT.keys()) + list(_ATTRIBUTES_DICT.keys())

    def __init__(
        self,
        source: NVEPathManager | Path | str,  # take path to db instead?
        validate: bool = True,
    ) -> None:
        """
        Initialize instance and set up obejcts and attributes used by this class.

        Among these is DataObjectManager, which creates and manages time series and curve objects.
        Various instace variables are used to cache objects.


        Args:
            source (Path): path manager to a database hierarchy where each database follows the
                           structure defined by DatabaseNames.
            validate (bool): Toggle data validation.

        """
        super().__init__()
        self._source: Path = self._set_source(source)
        self._validate = validate
        self.database_interpreter = _DatabaseInterpreter(self._source)
        self.data_object_manager = _DataObjectManager(validate=self._validate)

        self._attribute_objects: dict[str, Component | TimeVector | Curve | Expr | None] = {}
        self._data: dict[str, Component | TimeVector | Curve | Expr] = {}
        self._validation_errors: dict[str, dict[str, pd.DataFrame]] = {}

    def _set_source(self, source: NVEPathManager | Path | str) -> Path:
        self._check_type(source, (NVEPathManager, Path, str))
        path = source
        if isinstance(source, NVEPathManager):
            path = source.get_working_copy_path()
        return Path(path)

    def _populate(self) -> dict[str, Component | TimeVector | Curve | Expr]:
        t0 = time()
        t = time()
        self._populate_time_vectors()
        self.send_debug_event(f"---- TOTAL populate timevectors: {round(time() - t, 3)}")

        t = time()
        self._populate_curves()
        self.send_debug_event(f"---- TOTAL populate curves: {round(time() - t, 3)}")

        # populate attribute objects
        t = time()
        self._attribute_objects = self._populate_topology_objects(self._ATTRIBUTES_DICT, "ATTRIBUTE OBJECTS")

        self._data.update(self._populate_topology_objects(self._COMPONENT_DICT, "COMPONENTS"))
        self.send_debug_event(f"---- update data with components: {round(time() - t, 3)}")

        # needed for hydroaggregator and JulES
        t = time()
        set_global_energy_equivalent(self._data, "EnergyEqDownstream")
        self.send_debug_event(f"---- Calculating EnergyEqDownstream metadata: {round(time() - t, 3)}")

        self.send_debug_event(f"---- TOTAL TIME _populate: {round(time() - t0, 3)}")

        return self._data

    def _populate_time_vectors(self) -> None:
        """Create TimeVector objects and add them to the self._data dictionary."""
        self.send_debug_event("-------- TIME VECTORS --------")
        for timevector_tuple in self._TIME_VECTOR_LIST:
            database_id, require_whole_years = timevector_tuple
            self.send_debug_event(f"---- {database_id} ----")
            source, relative_loc = self.database_interpreter.get_source_and_relative_loc(database_id)

            if relative_loc is None:
                self.send_info_event(f"Could not find time vector file {database_id} in {source}. Skipping..")
                continue

            t = time()
            time_vectors = self.data_object_manager.create_time_vectors(source, relative_loc, require_whole_years)
            self.send_debug_event(f"Create {database_id} time vectors time: {round(time() - t, 3)}")

            for new_id in time_vectors:
                self._register_id(new_id, source / relative_loc)
            self._data.update(time_vectors)

    def _populate_curves(self) -> None:
        """Create TimeVector objects and add them to the self._data dictionary."""
        self.send_debug_event("-------- CURVES --------")
        for database_id in self._CURVE_LIST:
            self.send_debug_event(f"---- {database_id} ----")
            source, relative_loc = self.database_interpreter.get_source_and_relative_loc(database_id)
            if relative_loc is None:
                self.send_info_event(f"Could not find curve file {database_id} in {source}. Skipping..")
                continue

            t = time()
            curves = self.data_object_manager.create_curves(source, relative_loc)
            self.send_debug_event(f"Create {database_id} curves time: {round(time() - t, 3)}")

            for new_id in curves:
                self._register_id(new_id, source / relative_loc)
            self._data.update(curves)

    def _populate_topology_objects(
        self,
        names_mapping: dict[str, _BaseComponentsNames],
        object_type: str,
    ) -> dict[str, Component | tuple[object, dict]]:  # return components or tuples with attribute object and metadata.
        """Create Component or Attribute objects and add them to the self._data dictionary."""
        self.send_debug_event(f"-------- {object_type} --------")
        files_map = self._read_components_data(names_mapping)
        if self._validate:
            self._validate_files(files_map, names_mapping)

        return self._create_topology_objects(files_map, names_mapping)

    def _create_topology_objects(
        self,
        files_map: dict[str, tuple[pd.DataFrame, pd.DataFrame]],
        names_map: dict[str, _BaseComponentsNames],
    ) -> dict[str, Component]:
        components = {}
        self.send_info_event("Creating objects for Model...")
        t = time()
        for database_id, component_names in names_map.items():
            component_df, meta_df, relative_loc = files_map[database_id]

            component_returns = self._get_components(component_df, component_names, meta_df)

            for component, refs in component_returns:
                id_key = next(iter(component))
                self._register_id(id_key, relative_loc)
                self._register_references(id_key, refs)
                components.update(component)

        self.send_debug_event(f"Created objects in {round(time() - t, 3)} s")
        return components

    def _read_components_data(self, names_map: dict[str, _BaseComponentsNames]) -> dict[str, tuple[pd.DataFrame, pd.DataFrame]]:
        files_map: dict[str, tuple[pd.DataFrame, pd.DataFrame]] = {}
        self.send_info_event("Reading database files...")
        t = time()
        for database_id in names_map:
            source, relative_loc = self.database_interpreter.get_source_and_relative_loc(database_id)
            if relative_loc is None:
                self.send_info_event(f"Could not find attribute file {database_id} in {source}. Skipping..")
                continue
            files_map[database_id] = (*self.database_interpreter.read_attribute_table(database_id), relative_loc)

        self.send_debug_event(f"Read files in {round(time() - t, 3)} s")
        return files_map

    def _validate_files(self, files_map: dict[str, tuple[pd.DataFrame, pd.DataFrame]], names_map: dict[str, _BaseComponentsNames]) -> None:
        self.send_info_event("Validating database files...")
        t = time()
        for database_id, names_class in names_map.items():
            component_df, meta_df, relative_loc = files_map[database_id]

            errors = NVEEnergyModelPopulator._validate_component_data(names_class, component_df, meta_df)
            if errors:
                self._validation_errors[relative_loc] = errors
                continue

        if self._validation_errors:
            warnings, message = NVEEnergyModelPopulator._format_error_message(self._validation_errors)
            if warnings:
                self.send_warning_event(message)
            else:
                raise ValueError(message)

        self.send_debug_event(f"Validated files in {round(time() - t, 3)} s")

    def _get_components(
        self,
        df: pd.DataFrame,
        component_names: _BaseComponentsNames,
        meta_data: pd.DataFrame,
    ) -> tuple[dict[str, Component | tuple[object, dict[str, Meta]]], set[str]]:
        """
        Return objects from dataframe rows by calling a specific component creation function on each row.

        Args:
            create_component_function (Callable): Specialized function which creates a Component object from a single
                                                  row in the table dataframe.
            df (pd.DataFrame): Dataframe read from database.
            component_names (BaseComponentsNames): Class which contains the column names of the database table to
                                                   create objects from.
            meta_data (dict): List of dictionaries with metadata for the database tree of the relevant table.

        Returns:
            tuple[dict[str, Component], set[str]]: List of tuples containing dicts woth Component objects and their names/IDs, plus sets of references to other
                                                   objects in the data.

        """
        cols = list(df.columns)
        indices = {k: cols.index(k) for k in cols}
        meta_columns = {c for c in cols if c not in component_names.columns}
        return [
            (
                component_names.create_component(
                    row,
                    indices,
                    meta_columns=meta_columns,
                    meta_data=meta_data,
                    attribute_objects=self._attribute_objects,
                ),
                component_names.get_references(row, indices, component_names.ref_columns),
            )
            for row in df.to_numpy(dtype=object)
        ]  # Important to use dtype=object to keep types for checking later

    @staticmethod
    def _validate_component_data(
        component_names: _BaseComponentsNames,
        attribute_data: pd.DataFrame,
        meta_data: pd.DataFrame,
    ) -> dict[str, pd.DataFrame]:
        """
        Validate the attribute data and metadata of a component table.

        Args:
            component_names (BaseComponentsNames): Class which contains methods for validating attribute data and
                                                   metadata for a given database file.
            attribute_data (pd.DataFrame): Dataframe with attribute data for the given component.
            meta_data (pd.DataFrame): Dataframe with metadata.

        Returns:
            dict[str, pd.DataFrame]: Dictionary where values are dataframes with validation erros, and keys denote
                                     wheter the validation errors are in the attribute data or metadata. If no errors
                                     are found, an empty dictionary is returned.

        """
        attribute_data_schema = component_names.get_attribute_data_schema()
        meta_data_schema = component_names.get_metadata_schema()
        attribute_data_errors = component_names.validate(attribute_data_schema, attribute_data)
        meta_data_errors = component_names.validate(meta_data_schema, meta_data)

        errors = {}
        if attribute_data_errors is not None:
            errors["attribute data"] = attribute_data_errors
        if meta_data_errors is not None:
            errors["metadata"] = meta_data_errors
        return errors

    @staticmethod
    def _format_error_message(validation_errors: dict[str, dict[str, pd.DataFrame]]) -> tuple[bool, str]:
        """
        Format the validation errors into a readable message.

        Args:
            validation_errors (dict[str, pd.DataFrame]): Nested dictionary where keys are the relative database location
                                                         of the file, and values are dictionaries containing dataframes
                                                         with validation errors (values) for attribute data and metadata
                                                         (keys).

        Returns:
            warnings (bool): True if only warnings, False otherwise.
            message (str): Message containing all validation errors.

        """
        # If there are more than n errors, then the dataframes should be exported to a file and the message should
        # be different and contain a link to the folder/file.
        warnings = []
        message = ""
        for file_loc, errors in validation_errors.items():
            message += f"\nData validation failed for: {file_loc}"
            for data_type, failure_cases in errors.items():
                if all(failure_cases["is_warning"]):
                    message += f"\nWarnings found in {data_type}:\n"
                    warnings.append(True)
                else:
                    message += f"\nErrors found in {data_type}:\n"
                    warnings.append(False)
                message += f"{failure_cases}"

        warnings = bool(all(warnings))

        return warnings, message
