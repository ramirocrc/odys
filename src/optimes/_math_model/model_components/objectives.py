"""Objective function definitions for energy system optimization models.

This module defines objective function names and types used in energy system
optimization models.
"""

import linopy
import xarray as xr


class ObjectiveFuncions:
    def __init__(  # noqa: PLR0913
        self,
        var_generator_power: linopy.Variable,
        var_generator_startup: linopy.Variable,
        var_market_traded_vol: linopy.Variable,
        param_generator_variable_cost: xr.DataArray,
        param_generator_startup_cost: xr.DataArray,
        param_market_prices: xr.DataArray,
        param_scenario_probabilities: xr.DataArray,
    ) -> None:
        self.generator_power = var_generator_power
        self.generator_startup = var_generator_startup
        self.var_market_traded_vol = var_market_traded_vol
        self.generator_variable_cost = param_generator_variable_cost
        self.generator_startup_cost = param_generator_startup_cost
        self.param_market_prices = param_market_prices
        self.param_scenario_probabilities = param_scenario_probabilities

    @property
    def profit(self) -> linopy.LinearExpression:
        if self.param_market_prices is None:
            return -self.operating_cost
        return self.market_revenue - self.operating_cost

    @property
    def market_revenue(self) -> linopy.LinearExpression:
        return self.var_market_traded_vol * self.param_market_prices * self.param_scenario_probabilities  # pyright: ignore reportOperatorIssue

    @property
    def operating_cost(self) -> linopy.LinearExpression:
        scenario_cost = (
            self.generator_power * self.generator_variable_cost + self.generator_startup * self.generator_startup_cost  # pyright: ignore reportOperatorIssue
        )
        return scenario_cost * self.param_scenario_probabilities  # pyright: ignore reportOperatorIssue
