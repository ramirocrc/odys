"""MILP model representation for energy system optimization.

This module provides the EnergyMILPModel class that wraps a linopy Model
with typed accessors for energy system decision variables.
"""

from functools import cached_property

from linopy import Model, Variable
from pydantic import BaseModel, ConfigDict

from odys.math_model.model_components.parameters.battery_parameters import BatteryIndex
from odys.math_model.model_components.parameters.generator_parameters import GeneratorIndex
from odys.math_model.model_components.parameters.load_parameters import LoadIndex
from odys.math_model.model_components.parameters.market_parameters import MarketIndex
from odys.math_model.model_components.parameters.parameters import EnergySystemParameters
from odys.math_model.model_components.parameters.scenario_parameters import ScenarioIndex, TimeIndex
from odys.math_model.model_components.variables import ModelVariable


class EnergyModelIndices(BaseModel):
    """Collection of all dimension indices used in the optimization model."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    scenarios: ScenarioIndex
    time: TimeIndex
    generators: GeneratorIndex | None
    batteries: BatteryIndex | None
    loads: LoadIndex | None
    markets: MarketIndex | None


class EnergyMILPModel:
    """Wrapper around a linopy Model with typed variable accessors for energy systems."""

    def __init__(self, parameters: EnergySystemParameters) -> None:
        """Initialize the MILP model with energy system parameters.

        Args:
            parameters: Validated energy system parameters.

        """
        self._parameters = parameters
        self._linopy_model = Model(force_dim_names=True)

    @cached_property
    def indices(self) -> EnergyModelIndices:
        """Return all dimension indices for the model."""
        return EnergyModelIndices(
            scenarios=self._parameters.scenarios.scenario_index,
            time=self._parameters.scenarios.time_index,
            generators=self._parameters.generators.index if self._parameters.generators is not None else None,
            batteries=self._parameters.batteries.index if self._parameters.batteries is not None else None,
            loads=self._parameters.loads.index if self._parameters.loads is not None else None,
            markets=self._parameters.markets.index if self._parameters.markets is not None else None,
        )

    @property
    def linopy_model(self) -> Model:
        """Return the underlying linopy model."""
        return self._linopy_model

    @property
    def parameters(self) -> EnergySystemParameters:
        """Return the energy system parameters."""
        return self._parameters

    @property
    def generator_power(self) -> Variable:
        """Return the generator power output variable."""
        return self._linopy_model.variables[ModelVariable.GENERATOR_POWER.var_name]

    @property
    def generator_status(self) -> Variable:
        """Return the generator on/off status variable."""
        return self._linopy_model.variables[ModelVariable.GENERATOR_STATUS.var_name]

    @property
    def generator_startup(self) -> Variable:
        """Return the generator startup indicator variable."""
        return self._linopy_model.variables[ModelVariable.GENERATOR_STARTUP.var_name]

    @property
    def generator_shutdown(self) -> Variable:
        """Return the generator shutdown indicator variable."""
        return self._linopy_model.variables[ModelVariable.GENERATOR_SHUTDOWN.var_name]

    @property
    def battery_power_in(self) -> Variable:
        """Return the battery charging power variable."""
        return self._linopy_model.variables[ModelVariable.BATTERY_POWER_IN.var_name]

    @property
    def battery_power_net(self) -> Variable:
        """Return the battery net power variable (charge - discharge)."""
        return self._linopy_model.variables[ModelVariable.BATTERY_POWER_NET.var_name]

    @property
    def battery_power_out(self) -> Variable:
        """Return the battery discharging power variable."""
        return self._linopy_model.variables[ModelVariable.BATTERY_POWER_OUT.var_name]

    @property
    def battery_soc(self) -> Variable:
        """Return the battery state of charge variable."""
        return self._linopy_model.variables[ModelVariable.BATTERY_SOC.var_name]

    @property
    def battery_charge_mode(self) -> Variable:
        """Return the battery charge/discharge mode indicator variable."""
        return self._linopy_model.variables[ModelVariable.BATTERY_CHARGE_MODE.var_name]

    @property
    def market_sell_volume(self) -> Variable:
        """Return the market sell volume variable."""
        return self._linopy_model.variables[ModelVariable.MARKET_SELL.var_name]

    @property
    def market_buy_volume(self) -> Variable:
        """Return the market buy volume variable."""
        return self._linopy_model.variables[ModelVariable.MARKET_BUY.var_name]

    @property
    def market_trade_mode(self) -> Variable:
        """Return the market buy/sell mode indicator variable."""
        return self._linopy_model.variables[ModelVariable.MARKET_TRADE_MODE.var_name]
