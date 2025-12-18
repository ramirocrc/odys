"""Objective function definitions for energy system optimization models.

This module defines objective function names and types used in energy system
optimization models.
"""

import linopy

from odis._math_model.milp_model import EnergyMILPModel
from odis._math_model.model_components.sets import ModelDimension


class ObjectiveFunction:
    def __init__(self, milp_model: EnergyMILPModel) -> None:
        self._model = milp_model

    @property
    def profit(self) -> linopy.LinearExpression:
        profit = 0

        if self._model.parameters.scenarios.market_prices is not None:
            profit += self.get_market_revenue()  # ty: ignore

        if self._model.parameters.generators is not None:
            profit += -self.get_operating_costs()  # ty: ignore

        if isinstance(profit, int) and profit == 0:
            msg = "No terms added to profit"
            raise ValueError(msg)
        return profit  # ty: ignore

    def get_market_revenue(self) -> linopy.LinearExpression:
        return (
            (self._model.market_sell_volume - self._model.market_buy_volume)
            * self._model.parameters.scenarios.market_prices  # ty: ignore
            * self._model.parameters.scenarios.scenario_probabilities
        ).sum([ModelDimension.Scenarios, ModelDimension.Time, ModelDimension.Markets])

    def get_operating_costs(self) -> linopy.LinearExpression:
        return (
            self._model.generator_power * self._model.parameters.generators.variable_cost  # ty: ignore
            + self._model.generator_startup * self._model.parameters.generators.startup_cost  # ty: ignore
        ).sum([ModelDimension.Scenarios, ModelDimension.Time, ModelDimension.Generators])
