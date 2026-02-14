"""Objective function definitions for energy system optimization models.

This module defines objective function names and types used in energy system
optimization models.
"""

import linopy

from odys.math_model.milp_model import EnergyMILPModel
from odys.math_model.model_components.sets import ModelDimension


class ObjectiveFunction:
    """Builds the objective function for the energy system optimization model."""

    def __init__(self, milp_model: EnergyMILPModel) -> None:
        """Initialize with the MILP model to build the objective from."""
        self._model = milp_model

    @property
    def profit(self) -> linopy.LinearExpression:
        """Build the total profit expression (market revenue minus operating costs)."""
        profit = 0

        if self._model.parameters.scenarios.market_prices is not None:
            profit += self.get_market_revenue()

        if self._model.parameters.generators is not None:
            profit += -self.get_operating_costs()

        if isinstance(profit, int) and profit == 0:
            msg = "No terms added to profit"
            raise ValueError(msg)
        return profit

    def get_market_revenue(self) -> linopy.LinearExpression:
        """Calculate expected market revenue across all scenarios."""
        return (
            (self._model.market_sell_volume - self._model.market_buy_volume)  # pyrefly: ignore
            * self._model.parameters.scenarios.market_prices  # ty: ignore # pyrefly: ignore
            * self._model.parameters.scenarios.scenario_probabilities
        ).sum([ModelDimension.Scenarios, ModelDimension.Time, ModelDimension.Markets])

    def get_operating_costs(self) -> linopy.LinearExpression:
        """Calculate total generator operating costs (variable + startup)."""
        return (
            self._model.generator_power * self._model.parameters.generators.variable_cost  # ty: ignore # pyrefly: ignore
            + self._model.generator_startup * self._model.parameters.generators.startup_cost  # ty: ignore # pyrefly: ignore
        ).sum([ModelDimension.Scenarios, ModelDimension.Time, ModelDimension.Generators])
