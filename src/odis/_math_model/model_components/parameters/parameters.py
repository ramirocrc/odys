"""Parameter definitions for energy system optimization models.

This module defines parameter names and types used in energy system
optimization models.
"""

from pydantic import BaseModel

from odis._math_model.model_components.parameters.battery_parameters import BatteryParameters
from odis._math_model.model_components.parameters.generator_parameters import GeneratorParameters
from odis._math_model.model_components.parameters.load_parameters import LoadParameters
from odis._math_model.model_components.parameters.market_parameters import MarketParameters
from odis._math_model.model_components.parameters.scenario_parameters import ScenarioParameters


class EnergySystemParameters(BaseModel, frozen=True, extra="forbid", arbitrary_types_allowed=True):
    """Collection of all energy system parameters for optimization models."""

    generators: GeneratorParameters | None
    batteries: BatteryParameters | None
    loads: LoadParameters | None
    markets: MarketParameters | None
    scenarios: ScenarioParameters
