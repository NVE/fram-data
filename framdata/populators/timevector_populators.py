"""Contain classes for populating a Model with only TimeVectors."""

from pathlib import Path
from typing import ClassVar

import pandas as pd
from framcore.timevectors import LoadedTimeVector, TimeVector

from framdata.database_names.DatabaseNames import DatabaseNames as DbN
from framdata.populators._DatabaseInterpreter import _DatabaseInterpreter
from framdata.populators._DataObjectManager import _DataObjectManager
from framdata.populators.NVEEnergyModelPopulator import NVEEnergyModelPopulator
from framdata.populators.NVEPathManager import NVEPathManager


class NVETimeVectorPopulator(NVEEnergyModelPopulator):
    """
    Populate a Model with all time vectors defined in DatabaseNames if they exist.

    May be useful for experimenting with small scale networks of a few components, but still have acess to time vectors fileld with data.

    """

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
        (DbN.hydro_bypass_operationalbounds_restrictions, True),
        (DbN.hydro_inflow_profiles, True),
        (DbN.hydro_modules_operationalbounds_restrictions, True),
        (DbN.hydro_reservoirs_operationalbounds_restrictions, True),
    ]
    DATABASE_ID_LIST: ClassVar[list] = _TIME_VECTOR_LIST

    def __init__(
        self,
        source: NVEPathManager | Path | str,  # take path to db instead?
        validate: bool = True,
    ) -> None:
        """
        Initialize obejcts and attributes used by this class.

        Among these is DataObjectManager, which creates and manages time series and curve objects.
        Various instace attributes are used to cache objects.


        Args:
            source (Path): path manager to a database hierarchy where each database follows the
                           structure defined by DatabaseNames.
            validate (bool): Toggle data validation.

        """
        super().__init__(source, validate)
        self._source: Path = self._set_source(source)
        self._validate = validate
        self.database_interpreter = _DatabaseInterpreter(self._source)
        self.data_object_manager = _DataObjectManager(validate=self._validate)

        self._attribute_objects: dict[str, TimeVector | None] = {}
        self._data: dict[str, TimeVector] = {}
        self._validation_errors: dict[str, dict[str, pd.DataFrame]] = {}

    def _set_source(self, source: NVEPathManager | Path | str) -> Path:
        self._check_type(source, (NVEPathManager, Path, str))
        path = source
        if isinstance(source, NVEPathManager):
            path = source.get_working_copy_path()
        return Path(path)

    def _populate(self) -> dict[str, LoadedTimeVector]:
        self._populate_time_vectors()
        return self._data
