"""MILP model representation for energy system optimization.

This module provides the EnergyMILPModel class that wraps a linopy Model
with typed accessors for energy system decision variables.
"""

from datetime import timedelta
from functools import cached_property
from typing import cast

import linopy

from odys.domain.exceptions import OdysValidationError
from odys.optimization.model.dimensions import ModelDimension
from odys.parameters.energy_system_parameters import EnergySystemParameters


class VariableStore:
    """Typed view of linopy decision variables (explicit fields for autocomplete).

    Constructed from a linopy model after variables have been added. Field names
    are the linopy variable names from ``VariableDefinition.name``.
    """

    generator_power: linopy.Variable
    generator_status: linopy.Variable
    generator_startup: linopy.Variable
    generator_shutdown: linopy.Variable
    standalone_storage_power_in: linopy.Variable
    standalone_storage_net_power: linopy.Variable
    standalone_storage_power_out: linopy.Variable
    standalone_storage_soc: linopy.Variable
    standalone_storage_charge_mode: linopy.Variable
    ev_power_in: linopy.Variable
    ev_net_power: linopy.Variable
    ev_power_out: linopy.Variable
    ev_soc: linopy.Variable
    ev_charge_mode: linopy.Variable
    market_sell_volume: linopy.Variable
    market_buy_volume: linopy.Variable
    market_trade_mode: linopy.Variable
    load_adjustment: linopy.Variable
    charger_ev_assignment: linopy.Variable
    cvar_value_at_risk: linopy.Variable
    cvar_shortfall: linopy.Variable

    def __init__(self, linopy_model: linopy.Model) -> None:
        """Bind typed fields for variables present on the linopy model.

        Empty asset types omit their variables; accessing those fields raises
        ``AttributeError`` (same as a missing linopy key before G12).
        """
        variables = linopy_model.variables
        for var_name, var in variables.items():
            setattr(self, var_name, var)


class EnergyMILPModel:
    """Wrapper around a linopy Model with typed variable accessors for energy systems."""

    def __init__(self, parameters: EnergySystemParameters) -> None:
        """Initialize the MILP model with energy system parameters.

        Args:
            parameters: Validated energy system parameters.

        """
        self._parameters = parameters
        self._linopy_model = linopy.Model(force_dim_names=True)

    @cached_property
    def vars(self) -> VariableStore:
        """Return the typed decision-variable view (after variables are on the linopy model)."""
        return VariableStore(self._linopy_model)

    @property
    def linopy_model(self) -> linopy.Model:
        """Return the underlying linopy model."""
        return self._linopy_model

    @property
    def parameters(self) -> EnergySystemParameters:
        """Return the energy system parameters."""
        return self._parameters

    def per_scenario_profit(self) -> linopy.LinearExpression:
        """Profit per scenario, summed over time and assets but not over scenarios.

        Does not apply scenario probabilities; this is the raw per-scenario profit.
        Used in both the CVaR shortfall constraint and the CVaR objective term.
        """
        profit_terms: list[linopy.LinearExpression] = []

        if self._parameters.scenarios.market_prices is not None:
            profit_terms.append(
                (
                    (self.vars.market_sell_volume - self.vars.market_buy_volume)  # pyrefly: ignore
                    * self._parameters.scenarios.market_prices
                ).sum([ModelDimension.Time, ModelDimension.Markets]),
            )

        if self._parameters.generators is not None:
            profit_terms.append(
                -(
                    self.vars.generator_power * self._parameters.generators.variable_cost
                    + self.vars.generator_startup * self._parameters.generators.startup_cost
                    + self.vars.generator_shutdown * self._parameters.generators.shutdown_cost
                ).sum([ModelDimension.Time, ModelDimension.Generators]),
            )

        if self._parameters.flexible_loads is not None:
            profit_terms.append(
                (self.vars.load_adjustment * self._parameters.flexible_loads.value_of_consumption).sum(
                    [ModelDimension.Time, ModelDimension.FlexibleLoads],
                ),
            )

        if self._parameters.standalone_storages is not None:
            timestep_hours = self._parameters.timestep / timedelta(hours=1)
            profit_terms.append(
                -(
                    (self.vars.standalone_storage_power_in + self.vars.standalone_storage_power_out)
                    * timestep_hours
                    * self._parameters.standalone_storages.degradation_cost
                ).sum([ModelDimension.Time, ModelDimension.StandaloneStorages]),
            )

        if self._parameters.electric_vehicles is not None:
            timestep_hours = self._parameters.timestep / timedelta(hours=1)
            profit_terms.append(
                -(
                    (self.vars.ev_power_in + self.vars.ev_power_out)
                    * timestep_hours
                    * self._parameters.electric_vehicles.degradation_cost
                ).sum([ModelDimension.Time, ModelDimension.EVs]),
            )

        if not profit_terms:
            msg = (
                "per_scenario_profit requires at least one revenue or cost source "
                "(markets, generators, or flexible loads)"
            )
            raise OdysValidationError(msg)

        return cast("linopy.LinearExpression", sum(profit_terms))
