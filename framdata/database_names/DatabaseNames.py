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
    db01 = "db01_nodes_time_vectors"
    db10 = "db10_wind"
    db20 = "db20_solar"
    db30 = "db30_hydropower"
    db31 = "db31_hydropower_time_vectors"
    db32 = "db32_hydropower_curves"
    db40 = "db40_thermal"
    # db41 = "db41_thermal_time_vectors"
    db50 = "db50_demand"
    # db51 = "db51_demand_time_vectors"
    db60 = "db60_transmission"
    # db61 = "db61_transmission_time_vectors"

    db_folder_list: ClassVar[list] = [db00, db01, db10, db20, db30, db31, db32, db40, db50, db60]

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

    # ==== WIND ====
    wind_generators = "Wind.Generators"
    wind_generators_capacity = "Wind.Generators.capacity"
    wind_generators_profiles = "Wind.Generators.profiles"

    # ==== SOLAR ====
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
        hydro_modules: db30,
        hydro_modules_volumecapacity: db30,
        hydro_modules_enekv_global_derived: db30,
        hydro_modules_reggrad_glob_derived: db30,
        hydro_modules_reggrad_lok_derived: db30,
        hydro_bypass: db30,
        hydro_generators: db30,
        hydro_inflow: db30,
        hydro_inflow_yearvolume: db30,
        hydro_inflow_upstream_inflow_derived: db30,
        hydro_pumps: db30,
        hydro_reservoirs: db30,
        # hydro time series
        hydro_inflow_profiles: db31,
        hydro_bypass_operationalbounds_restrictions: db31,
        hydro_modules_operationalbounds_restrictions: db31,
        hydro_reservoirs_operationalbounds_restrictions: db31,
        hydro_generators_energyeq_mid: db31,
        # hydro curves
        hydro_curves: db32,
        hydro_pqcurves: db32,
        # ==== THERMAL ====,
        thermal_generators: db40,
        thermal_generators_capacity: db40,
        thermal_generators_profiles: db40,
        # ==== DEMAND ====,
        demand_consumers: db50,
        demand_consumers_capacity: db50,
        demand_consumers_normalprices: db50,
        demand_consumers_profiles_weatheryears: db50,
        demand_consumers_profiles_oneyear: db50,
        # ==== WIND ====,
        wind_generators: db10,
        wind_generators_capacity: db10,
        wind_generators_profiles: db10,
        # ==== SOLAR ====
        solar_generators: db20,
        solar_generators_capacity: db20,
        solar_generators_profiles: db20,
        # ==== Transmission ====
        transmission_grid: db60,
        transmission_capacity: db60,
        transmission_loss: db60,
        transmission_profiles: db60,
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
