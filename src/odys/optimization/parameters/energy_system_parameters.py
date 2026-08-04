"""Parameter definitions for energy system optimization models.

This module defines parameter names and types used in energy system
optimization models.
"""

from datetime import timedelta

from pydantic import BaseModel, ConfigDict

from odys.domain.objective import Objective
from odys.optimization.parameters.entity_parameters.charger_parameters import ChargerParameters
from odys.optimization.parameters.entity_parameters.electric_vehicle_parameters import ElectricVehicleParameters
from odys.optimization.parameters.entity_parameters.flexible_load_parameters import FlexibleLoadParameters
from odys.optimization.parameters.entity_parameters.generator_parameters import GeneratorParameters
from odys.optimization.parameters.entity_parameters.market_parameters import MarketParameters
from odys.optimization.parameters.entity_parameters.scenario_parameters import ScenarioParameters
from odys.optimization.parameters.entity_parameters.standalone_storage_parameters import StandaloneStorageParameters


class EnergySystemParameters(BaseModel):
    """Collection of all energy system parameters for optimization models."""

    model_config = ConfigDict(frozen=True, extra="forbid", arbitrary_types_allowed=True)

    timestep: timedelta
    generators: GeneratorParameters
    standalone_storages: StandaloneStorageParameters
    flexible_loads: FlexibleLoadParameters
    markets: MarketParameters
    scenarios: ScenarioParameters
    chargers: ChargerParameters
    electric_vehicles: ElectricVehicleParameters
    objective: Objective

    @property
    def has_generators(self) -> bool:
        """Return True if there are generators."""
        return not self.generators.is_empty

    @property
    def has_standalone_storages(self) -> bool:
        """Return True if there are standalone storages."""
        return not self.standalone_storages.is_empty

    @property
    def has_flexible_loads(self) -> bool:
        """Return True if there are flexible loads."""
        return not self.flexible_loads.is_empty

    @property
    def has_markets(self) -> bool:
        """Return True if there are markets."""
        return not self.markets.is_empty

    @property
    def has_chargers(self) -> bool:
        """Return True if there are chargers."""
        return not self.chargers.is_empty

    @property
    def has_electric_vehicles(self) -> bool:
        """Return True if there are electric vehicles."""
        return not self.electric_vehicles.is_empty
