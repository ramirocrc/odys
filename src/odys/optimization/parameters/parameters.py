"""Parameter definitions for energy system optimization models.

This module defines parameter names and types used in energy system
optimization models.
"""

from datetime import timedelta

from pydantic import BaseModel, ConfigDict

from odys.domain.objective import Objective
from odys.optimization.parameters.charger_parameters import ChargerParameters
from odys.optimization.parameters.electric_vehicle_parameters import ElectricVehicleParameters
from odys.optimization.parameters.flexible_load_parameters import FlexibleLoadParameters
from odys.optimization.parameters.generator_parameters import GeneratorParameters
from odys.optimization.parameters.market_parameters import MarketParameters
from odys.optimization.parameters.scenario_parameters import ScenarioParameters
from odys.optimization.parameters.standalone_storage_parameters import StandaloneStorageParameters


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
