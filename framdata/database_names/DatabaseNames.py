"""Container for names and locations of files and folders in the NVE database."""

from pathlib import Path
from typing import ClassVar

from framcore import Base


class DatabaseNames(Base):
    """Define names of files and folders in the NVE database and map files to folders."""

    # ---------- FILE EXTENSIONS ---------- #
    ext_excel = ".xlsx"
    ext_h5 = ".h5"
    ext_parquet = ".parquet"
    ext_yaml = ".yaml"

    # ---------- SHEETS ---------- #
    data_sheet = "Data"
    metadata_sheet = "Metadata"

    # ---------- SUFFIXES ---------- #
    capacity = ".capacity"
    prices = ".prices"
    profiles = ".profiles"
    curves = ".curves"

    # ---------- DATABASE FOLDERs MAP ---------- #
    db00 = "db00_nodes"
    db01 = "db01_nodes_profiles"
    db10 = "db10_wind_solar"
    db11 = "db11_wind_solar_profiles"
    db20 = "db20_hydropower"
    db21 = "db21_hydropower_profiles"
    db22 = "db22_hydropower_curves"
    db30 = "db30_thermal"
    db31 = "db31_thermal_profiles"
    db40 = "db40_demand"
    db41 = "db41_demand_profiles"
    db50 = "db50_transmission"
    db51 = "db51_transmission_profiles"

    db_folder_list: ClassVar[list] = [db00, db01, db10, db11, db20, db21, db22, db30, db31, db40, db41, db50, db51]

    # ---------- FILENAMES ---------- #
    # ==== NODES ====
    power_nodes = "Power.Nodes"
    power_nodes_prices = "Power.Nodes.prices"
    power_nodes_profiles = "Power.Nodes.profiles"

    fuel_nodes = "Fuel.Nodes"
    fuel_nodes_prices = "Fuel.Nodes.prices"
    fuel_nodes_profiles = "Fuel.Nodes.profiles"

    emission_nodes = "Emission.Nodes"
    emission_nodes_prices = "Emission.Nodes.prices"
    emission_nodes_profiles = "Emission.Nodes.profiles"

    # ==== THERMAL ====
    thermal_generators = "Thermal.Generators"
    thermal_generators_capacity = "Thermal.Generators.capacity"
    thermal_generators_profiles = "Thermal.Generators.profiles"

    # ==== HYDROPOWER ====
    # hydro attribute tables
    hydro_modules = "Hydropower.Modules"
    hydro_modules_volumecapacity = "Hydropower.Modules.VolumeCapacity"
    hydro_modules_enekv_global_derived = "Hydropower.Modules.enekv_global_derived"
    hydro_modules_reggrad_glob_derived = "Hydropower.Modules.reggrad_glob_derived"
    hydro_modules_reggrad_lok_derived = "Hydropower.Modules.reggrad_lok_derived"
    hydro_bypass = "Hydropower.Bypass"
    hydro_generators = "Hydropower.Generators"
    hydro_inflow = "Hydropower.Inflow"
    hydro_inflow_yearvolume = "Hydropower.Inflow.YearVolume"
    hydro_inflow_upstream_inflow_derived = "Hydropower.Inflow.upstream_inflow_derived"
    hydro_pumps = "Hydropower.Pumps"
    hydro_reservoirs = "Hydropower.Reservoirs"

    # hydro time series
    hydro_inflow_profiles = "Hydropower.Inflow.profiles"
    hydro_bypass_operationalbounds_restrictions = "Hydropower.Bypass.OperationalBounds.Restrictions"
    hydro_modules_operationalbounds_restrictions = "Hydropower.Modules.OperationalBounds.Restrictions"
    hydro_reservoirs_operationalbounds_restrictions = "Hydropower.Reservoirs.OperationalBounds.Restrictions"
    hydro_generators_energyeq_mid = "Hydropower.Generators.EnergyEq_mid"

    # hydro curves
    hydro_curves = "Hydropower.curves"
    hydro_pqcurves = "Hydropower.pqcurves"

    # ==== DEMAND ====
    demand_consumers = "Demand.Consumers"
    demand_consumers_capacity = "Demand.Consumers.capacity"
    demand_consumers_normalprices = "Demand.Consumers.normalprices"
    demand_consumers_profiles_weatheryears = "Demand.Consumers.profiles.weatheryears"
    demand_consumers_profiles_oneyear = "Demand.Consumers.profiles"

    # ==== WIND AND SOLAR ====
    wind_generators = "Wind.Generators"
    wind_generators_capacity = "Wind.Generators.capacity"
    wind_generators_profiles = "Wind.Generators.profiles"
    solar_generators = "Solar.Generators"
    solar_generators_capacity = "Solar.Generators.capacity"
    solar_generators_profiles = "Solar.Generators.profiles"

    # ==== Transmission ====
    transmission_grid = "Transmission.Grid"
    transmission_capacity = transmission_grid + ".capacity"
    transmission_loss = transmission_grid + ".loss"
    transmission_profiles = transmission_grid + ".profiles"

    # ---------- DATABASE FOLDER MAP ---------- #
    db_folder_map: ClassVar[dict[str, list[str]]] = {
        # ===: NODES ====,
        power_nodes: db00,
        fuel_nodes: db00,
        emission_nodes: db00,
        power_nodes_prices: db01,
        fuel_nodes_prices: db01,
        emission_nodes_prices: db01,
        power_nodes_profiles: db01,
        fuel_nodes_profiles: db01,
        emission_nodes_profiles: db01,
        # ===: HYDROPOWER ====,
        # hydro attribute tables
        hydro_modules: db20,
        hydro_modules_volumecapacity: db20,
        hydro_modules_enekv_global_derived: db20,
        hydro_modules_reggrad_glob_derived: db20,
        hydro_modules_reggrad_lok_derived: db20,
        hydro_bypass: db20,
        hydro_generators: db20,
        hydro_inflow: db20,
        hydro_inflow_yearvolume: db20,
        hydro_inflow_upstream_inflow_derived: db20,
        hydro_pumps: db20,
        hydro_reservoirs: db20,
        # hydro time series
        hydro_inflow_profiles: db21,
        hydro_bypass_operationalbounds_restrictions: db21,
        hydro_modules_operationalbounds_restrictions: db21,
        hydro_reservoirs_operationalbounds_restrictions: db21,
        hydro_generators_energyeq_mid: db21,
        # hydro curves
        hydro_curves: db22,
        hydro_pqcurves: db22,
        # ===: THERMAL ====,
        thermal_generators: db30,
        thermal_generators_capacity: db30,
        thermal_generators_profiles: db31,
        # ===: DEMAND ====,
        demand_consumers: db40,
        demand_consumers_capacity: db40,
        demand_consumers_normalprices: db40,
        demand_consumers_profiles_weatheryears: db41,
        demand_consumers_profiles_oneyear: db41,
        # ===: WIND AND SOLAR ====,
        wind_generators: db10,
        wind_generators_capacity: db11,
        wind_generators_profiles: db11,
        solar_generators: db10,
        solar_generators_capacity: db11,
        solar_generators_profiles: db11,
        # ==== Transmission ====
        transmission_grid: db50,
        transmission_capacity: db51,
        transmission_loss: db51,
        transmission_profiles: db51,
    }

    @classmethod
    def get_relative_folder_path(cls, file_id: str) -> Path:
        """
        Get the relative database folder path for a given file_id.

        The relative path consists of database folder and file name.

        Args:
            file_id (str): Identifier for the file to retrieve.

        Returns:
            Path: The database folder name.

        """
        try:
            return Path(cls.db_folder_map[file_id])
        except KeyError as e:
            message = f"File id '{file_id}' not found in database folder map."

            raise KeyError(message) from e

    @classmethod
    def get_file_name(cls, source: Path, db_folder: str, file_id: str) -> str | None:
        """
        Get the name of a file, with extension, from a file ID and a path.

        Args:
            source (Path): Root path of the database.
            db_folder (str): Database folder to look for the file in.
            file_id (str): ID of file, i.e the name of the file without extension.

        Raises:
            RuntimeError: If multiple files with the same ID but different extensions are found.

        Returns:
            str | None: File ID and extension combined. If file is not found, return None.

        """
        db_path = source / db_folder
        if not db_path.exists():
            message = f"The database folder {db_path} does not exist."
            raise FileNotFoundError(message)
        candidate_extentions = set()
        for file_path in db_path.iterdir():
            if file_path.is_file() and file_path.stem == file_id:
                candidate_extentions.add(file_path.suffix)
        if len(candidate_extentions) > 1:  # Multiple files of same ID. Ambiguous
            message = (
                f"Found multiple files with ID {file_id} (with different extensions: {candidate_extentions}) in database folder {db_path}."
                " File names must be unique."
            )
            raise RuntimeError(message)
        if len(candidate_extentions) == 0:  # No matching files.
            return None
            # message = f"Found no file with ID {file_id} in database folder {db_path}."
            # raise FileNotFoundError(message)

        (extension,) = candidate_extentions  # We have only one candidate, so we extract it.
        return file_id + extension
