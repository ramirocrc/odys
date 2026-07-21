"""Parameter definitions for energy system optimization models.

This module defines parameter names and types used in energy system
optimization models.
"""

from datetime import timedelta

from pydantic import BaseModel, ConfigDict

from odys.domain.objective import Objective
from odys.optimization.parameters.flexible_load_parameters import FlexibleLoadParameters
from odys.optimization.parameters.generator_parameters import GeneratorParameters
from odys.optimization.parameters.market_parameters import MarketParameters
from odys.optimization.parameters.scenario_parameters import ScenarioParameters
from odys.optimization.parameters.storage_parameters import StorageParameters


class EnergySystemParameters(BaseModel):
    """Collection of all energy system parameters for optimization models."""

    model_config = ConfigDict(frozen=True, extra="forbid", arbitrary_types_allowed=True)

    timestep: timedelta
    generators: GeneratorParameters
    storages: StorageParameters
    flexible_loads: FlexibleLoadParameters
    markets: MarketParameters
    scenarios: ScenarioParameters
    objective: Objective

    @property
    def has_generators(self) -> bool:
        """Return True if there are generators."""
        return not self.generators.is_empty

    @property
    def has_storages(self) -> bool:
        """Return True if there are storages."""
        return not self.storages.is_empty

    @property
    def has_flexible_loads(self) -> bool:
        """Return True if there are flexible loads."""
        return not self.flexible_loads.is_empty

    @property
    def has_markets(self) -> bool:
        """Return True if there are markets."""
        return not self.markets.is_empty
