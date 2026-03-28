"""MILP model representation for energy system optimization.

This module provides the EnergyMILPModel class that wraps a linopy Model
with typed accessors for energy system decision variables.
"""

from functools import cached_property

import linopy
from linopy import Model, Variable
from pydantic import BaseModel, ConfigDict

from odys.math_model.model_components.parameters.generator_parameters import GeneratorIndex
from odys.math_model.model_components.parameters.load_parameters import LoadIndex
from odys.math_model.model_components.parameters.market_parameters import MarketIndex
from odys.math_model.model_components.parameters.parameters import EnergySystemParameters
from odys.math_model.model_components.parameters.scenario_parameters import ScenarioIndex, TimeIndex
from odys.math_model.model_components.parameters.storage_parameters import StorageIndex
from odys.math_model.model_components.sets import ModelDimension
from odys.math_model.model_components.variables import ModelVariable


class EnergyModelIndices(BaseModel):
    """Collection of all dimension indices used in the optimization model."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    scenarios: ScenarioIndex
    time: TimeIndex
    generators: GeneratorIndex | None
    storages: StorageIndex | None
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
            storages=self._parameters.storages.index if self._parameters.storages is not None else None,
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
    def storage_power_in(self) -> Variable:
        """Return the storage charging power variable."""
        return self._linopy_model.variables[ModelVariable.STORAGE_POWER_IN.var_name]

    @property
    def storage_power_net(self) -> Variable:
        """Return the storage net power variable (charge - discharge)."""
        return self._linopy_model.variables[ModelVariable.STORAGE_POWER_NET.var_name]

    @property
    def storage_power_out(self) -> Variable:
        """Return the storage discharging power variable."""
        return self._linopy_model.variables[ModelVariable.STORAGE_POWER_OUT.var_name]

    @property
    def storage_soc(self) -> Variable:
        """Return the storage state of charge variable."""
        return self._linopy_model.variables[ModelVariable.STORAGE_SOC.var_name]

    @property
    def storage_charge_mode(self) -> Variable:
        """Return the storage charge/discharge mode indicator variable."""
        return self._linopy_model.variables[ModelVariable.STORAGE_CHARGE_MODE.var_name]

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

    @property
    def cvar_value_at_risk(self) -> Variable:
        """Return the value at risk, scalar variable."""
        return self._linopy_model.variables[ModelVariable.VALUE_AT_RISK.var_name]

    @property
    def cvar_shortfall(self) -> Variable:
        """Return the revenue shortfall revenue variable."""
        return self._linopy_model.variables[ModelVariable.SHORTFALL_REVENUE.var_name]

    def per_scenario_profit(self) -> linopy.LinearExpression:
        """Profit per scenario, summed over time and assets but not over scenarios.

        Does not apply scenario probabilities — this is the raw per-scenario profit.
        Used in both the CVaR shortfall constraint and the CVaR objective term.
        """
        profit_terms: list[linopy.LinearExpression] = []

        if self._parameters.scenarios.market_prices is not None:
            profit_terms.append(
                (
                    (self.market_sell_volume - self.market_buy_volume)  # pyrefly: ignore
                    * self._parameters.scenarios.market_prices
                ).sum([ModelDimension.Time, ModelDimension.Markets]),
            )

        if self._parameters.generators is not None:
            profit_terms.append(
                -(
                    self.generator_power * self._parameters.generators.variable_cost
                    + self.generator_startup * self._parameters.generators.startup_cost
                ).sum([ModelDimension.Time, ModelDimension.Generators]),
            )
        if not profit_terms:
            msg = "per_scenario_profit requires at least one revenue or cost source (markets or generators)"
            raise ValueError(msg)

        return sum(profit_terms)  # type: ignore[return-value]
