"""Objective function definitions for energy system optimization models.

This module defines objective function names and types used in energy system
optimization models.
"""

import linopy

from optimes._math_model.milp_model import EnergyMILPModel


class ObjectiveFuncions:
    def __init__(self, milp_model: EnergyMILPModel) -> None:
        self._model = milp_model

    @property
    def profit(self) -> linopy.LinearExpression:
        profit = None

        if self._model.parameters.scenario.market_prices is not None:
            profit = self.get_market_revenue()

        if self._model.parameters.generators is not None:
            operating_cost = self.get_operating_costs()
            profit = -operating_cost if profit is None else profit - operating_cost

        if profit is None:
            msg = "No terms added to profit"
            raise ValueError(msg)
        return profit

    def get_market_revenue(self) -> linopy.LinearExpression:
        return (
            self._model.market_traded_volume  # pyright: ignore reportOperatorIssue
            * self._model.parameters.scenario.market_prices  # pyright: ignore reportOperatorIssue
            * self._model.parameters.scenario.scenario_probabilities
        )

    def get_operating_costs(self) -> linopy.LinearExpression:
        return (
            self._model.generator_power * self._model.parameters.generators.variable_cost  # pyright: ignore reportOperatorIssue
            + self._model.generator_startup * self._model.parameters.generators.startup_cost  # pyright: ignore reportOperatorIssue
        )
