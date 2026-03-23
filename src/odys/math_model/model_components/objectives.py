"""Objective function definitions for energy system optimization models.

This module defines objective function names and types used in energy system
optimization models.
"""

import linopy

from odys.math_model.milp_model import EnergyMILPModel
from odys.math_model.model_components.sets import ModelDimension


def profit_term(model: EnergyMILPModel) -> linopy.LinearExpression:
    """Build the profit expression."""
    scenario_probability = model.parameters.scenarios.scenario_probabilities
    return (model.per_scenario_profit() * scenario_probability).sum(ModelDimension.Scenarios)


def cvar_term(model: EnergyMILPModel) -> linopy.LinearExpression:
    """Build the CVaR expression: η - 1/(1-alpha) * Σ_s p_s * z_s."""
    confidence_level = model.parameters.cvar_config.confidence_level  # type: ignore[union-attr]
    probs = model.parameters.scenarios.scenario_probabilities
    expected_shortfall = (probs * model.cvar_shortfall).sum(ModelDimension.Scenarios)
    return model.cvar_value_at_risk - (1 / (1 - confidence_level)) * expected_shortfall


def build_objective(milp_model: EnergyMILPModel) -> linopy.LinearExpression:
    """Build the full objective function, including the CVaR term if configured."""
    objective = profit_term(milp_model)

    cvar_config = milp_model.parameters.cvar_config

    if cvar_config is None:
        return objective

    return objective + cvar_config.weight * cvar_term(milp_model)
