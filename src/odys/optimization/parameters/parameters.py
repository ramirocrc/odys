"""Parameter definitions for energy system optimization models.

This module defines parameter names and types used in energy system
optimization models.
"""

from datetime import timedelta

from pydantic import BaseModel, ConfigDict

from odys.domain.objective import Objective
from odys.optimization.parameters.generator_parameters import GeneratorParameters
from odys.optimization.parameters.load_parameters import LoadParameters
from odys.optimization.parameters.market_parameters import MarketParameters
from odys.optimization.parameters.scenario_parameters import ScenarioParameters
from odys.optimization.parameters.storage_parameters import StorageParameters


class EnergySystemParameters(BaseModel):
    """Collection of all energy system parameters for optimization models."""

    model_config = ConfigDict(frozen=True, extra="forbid", arbitrary_types_allowed=True)

    timestep: timedelta
    generators: GeneratorParameters | None
    storages: StorageParameters | None
    loads: LoadParameters | None
    markets: MarketParameters | None
    scenarios: ScenarioParameters
    objective: Objective
