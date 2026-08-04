"""MILP model representation for energy system optimization.

This module provides the EnergyMILPModel class that wraps a linopy Model
with typed accessors for energy system decision variables.
"""

from datetime import timedelta
from functools import cached_property
from typing import cast

import linopy
from linopy import Model, Variable
from pydantic import BaseModel, ConfigDict

from odys.domain.exceptions import OdysValidationError
from odys.optimization.model.sets import ModelDimension, ModelIndex
from odys.optimization.parameters.energy_system_parameters import EnergySystemParameters
from odys.optimization.parameters.entity_parameters.charger_parameters import ChargerIndex
from odys.optimization.parameters.entity_parameters.electric_vehicle_parameters import ElectricVehicleIndex
from odys.optimization.parameters.entity_parameters.flexible_load_parameters import FlexibleLoadIndex
from odys.optimization.parameters.entity_parameters.generator_parameters import GeneratorIndex
from odys.optimization.parameters.entity_parameters.market_parameters import MarketIndex
from odys.optimization.parameters.entity_parameters.scenario_parameters import ScenarioIndex, TimeIndex
from odys.optimization.parameters.entity_parameters.standalone_storage_parameters import StandaloneStorageIndex


class EnergyModelIndices(BaseModel):
    """Collection of all dimension indices used in the optimization model."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    scenarios: ScenarioIndex
    time: TimeIndex
    generators: GeneratorIndex
    standalone_storages: StandaloneStorageIndex
    flexible_loads: FlexibleLoadIndex
    markets: MarketIndex
    chargers: ChargerIndex
    electric_vehicles: ElectricVehicleIndex

    def get_index(self, dimension: ModelDimension) -> ModelIndex:
        """Return the index for a given dimension."""
        mapping = {
            ModelDimension.Scenarios: self.scenarios,
            ModelDimension.Time: self.time,
            ModelDimension.Generators: self.generators,
            ModelDimension.StandaloneStorages: self.standalone_storages,
            ModelDimension.FlexibleLoads: self.flexible_loads,
            ModelDimension.Markets: self.markets,
            ModelDimension.Chargers: self.chargers,
            ModelDimension.EVs: self.electric_vehicles,
        }
        return mapping[dimension]


class ModelVariables:
    """Typed view of linopy decision variables (explicit fields for autocomplete).

    Constructed from a linopy model after variables have been added. Field names
    are the linopy variable names from ``VariableSpec.name``.
    """

    __slots__ = [
        "charger_ev_assignment",
        "cvar_shortfall",
        "cvar_value_at_risk",
        "ev_charge_mode",
        "ev_net_power",
        "ev_power_in",
        "ev_power_out",
        "ev_soc",
        "generator_power",
        "generator_shutdown",
        "generator_startup",
        "generator_status",
        "load_adjustment",
        "market_buy_volume",
        "market_sell_volume",
        "market_trade_mode",
        "standalone_storage_charge_mode",
        "standalone_storage_net_power",
        "standalone_storage_power_in",
        "standalone_storage_power_out",
        "standalone_storage_soc",
    ]
    generator_power: Variable
    generator_status: Variable
    generator_startup: Variable
    generator_shutdown: Variable
    standalone_storage_power_in: Variable
    standalone_storage_net_power: Variable
    standalone_storage_power_out: Variable
    standalone_storage_soc: Variable
    standalone_storage_charge_mode: Variable
    ev_power_in: Variable
    ev_net_power: Variable
    ev_power_out: Variable
    ev_soc: Variable
    ev_charge_mode: Variable
    market_sell_volume: Variable
    market_buy_volume: Variable
    market_trade_mode: Variable
    load_adjustment: Variable
    charger_ev_assignment: Variable
    cvar_value_at_risk: Variable
    cvar_shortfall: Variable

    def __init__(self, linopy_model: Model) -> None:
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
        self._linopy_model = Model(force_dim_names=True)

    @cached_property
    def indices(self) -> EnergyModelIndices:
        """Return all dimension indices for the model."""
        return EnergyModelIndices(
            scenarios=self._parameters.scenarios.scenario_index,
            time=self._parameters.scenarios.time_index,
            generators=self._parameters.generators.index,
            standalone_storages=self._parameters.standalone_storages.index,
            flexible_loads=self._parameters.flexible_loads.index,
            markets=self._parameters.markets.index,
            chargers=self._parameters.chargers.index,
            electric_vehicles=self._parameters.electric_vehicles.index,
        )

    @cached_property
    def vars(self) -> ModelVariables:
        """Return the typed decision-variable view (after variables are on the linopy model)."""
        return ModelVariables(self._linopy_model)

    @property
    def linopy_model(self) -> Model:
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

        if not self._parameters.generators.is_empty:
            profit_terms.append(
                -(
                    self.vars.generator_power * self._parameters.generators.variable_cost
                    + self.vars.generator_startup * self._parameters.generators.startup_cost
                    + self.vars.generator_shutdown * self._parameters.generators.shutdown_cost
                ).sum([ModelDimension.Time, ModelDimension.Generators]),
            )

        if not self._parameters.flexible_loads.is_empty:
            profit_terms.append(
                (self.vars.load_adjustment * self._parameters.flexible_loads.value_of_consumption).sum(
                    [ModelDimension.Time, ModelDimension.FlexibleLoads],
                ),
            )

        if not self._parameters.standalone_storages.is_empty:
            timestep_hours = self._parameters.timestep / timedelta(hours=1)
            profit_terms.append(
                -(
                    (self.vars.standalone_storage_power_in + self.vars.standalone_storage_power_out)
                    * timestep_hours
                    * self._parameters.standalone_storages.degradation_cost
                ).sum([ModelDimension.Time, ModelDimension.StandaloneStorages]),
            )

        if not self._parameters.electric_vehicles.is_empty:
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
