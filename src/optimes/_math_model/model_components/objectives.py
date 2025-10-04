"""Objective function definitions for energy system optimization models.

This module defines objective function names and types used in energy system
optimization models.
"""

import linopy
import xarray as xr

SECONDS_IN_HOUR = 3600


def get_operating_costs(
    var_generator_power: linopy.Variable,
    var_generator_startup: linopy.Variable,
    param_generator_variable_cost: xr.DataArray,
    param_generator_startup_cost: xr.DataArray,
    scenario_probabilities: xr.DataArray,
) -> linopy.LinearExpression:
    costs = var_generator_power * param_generator_variable_cost + var_generator_startup * param_generator_startup_cost  # pyright: ignore reportOperatorIssue
    return costs * scenario_probabilities  # pyright: ignore reportOperatorIssue
