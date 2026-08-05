"""Parameter definitions for energy system optimization models.

This module defines the EnergySystemParameters bag that holds all
parameters needed by the optimization model.
"""

from datetime import timedelta

from pydantic import BaseModel, ConfigDict

from odys.domain.objective import Objective
from odys.optimization.model.indices import EnergyModelCoordinates
from odys.optimization.parameters.entity_parameters.charger_parameters import ChargerParameters
from odys.optimization.parameters.entity_parameters.electric_vehicle_parameters import ElectricVehicleParameters
from odys.optimization.parameters.entity_parameters.flexible_load_parameters import FlexibleLoadParameters
from odys.optimization.parameters.entity_parameters.generator_parameters import GeneratorParameters
from odys.optimization.parameters.entity_parameters.market_parameters import MarketParameters
from odys.optimization.parameters.entity_parameters.scenario_parameters import ScenarioParameters
from odys.optimization.parameters.entity_parameters.standalone_storage_parameters import StandaloneStorageParameters


class EnergySystemParameters(BaseModel):
    """Collection of all energy system parameters for optimization models.

    Time and scenario coordinates are always present. Asset parameter blocks
    are present only when the corresponding asset type exists in the portfolio.
    """

    model_config = ConfigDict(frozen=True, extra="forbid", arbitrary_types_allowed=True)

    timestep: timedelta
    objective: Objective
    scenarios: ScenarioParameters
    coordinates: EnergyModelCoordinates

    generators: GeneratorParameters | None = None
    standalone_storages: StandaloneStorageParameters | None = None
    flexible_loads: FlexibleLoadParameters | None = None
    markets: MarketParameters | None = None
    chargers: ChargerParameters | None = None
    electric_vehicles: ElectricVehicleParameters | None = None
