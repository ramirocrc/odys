"""Parameter definitions for energy system optimization models.

This module defines parameter names and types used in energy system
optimization models.
"""

from pydantic import BaseModel, ConfigDict

from odys._math_model.model_components.parameters.battery_parameters import BatteryParameters
from odys._math_model.model_components.parameters.generator_parameters import GeneratorParameters
from odys._math_model.model_components.parameters.load_parameters import LoadParameters
from odys._math_model.model_components.parameters.market_parameters import MarketParameters
from odys._math_model.model_components.parameters.scenario_parameters import ScenarioParameters


class EnergySystemParameters(BaseModel):
    """Collection of all energy system parameters for optimization models."""

    model_config = ConfigDict(frozen=True, extra="forbid", arbitrary_types_allowed=True)

    generators: GeneratorParameters | None
    batteries: BatteryParameters | None
    loads: LoadParameters | None
    markets: MarketParameters | None
    scenarios: ScenarioParameters
