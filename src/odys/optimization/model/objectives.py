"""Objective function definitions for energy system optimization models."""

import linopy

from odys.domain.objective import CVaRTerm, Objective
from odys.optimization.model.dimensions import ModelDimension
from odys.optimization.model.milp_model import EnergyMILPModel


def _profit_expr(model: EnergyMILPModel) -> linopy.LinearExpression:
    probs = model.parameters.scenarios.scenario_probabilities
    return (model.per_scenario_profit() * probs).sum(ModelDimension.Scenarios)


def _cvar_expr(model: EnergyMILPModel, cvar: CVaRTerm) -> linopy.LinearExpression:
    probs = model.parameters.scenarios.scenario_probabilities
    expected_shortfall = (probs * model.vars.cvar_shortfall).sum(ModelDimension.Scenarios)
    cvar_expr: linopy.LinearExpression = (
        model.vars.cvar_value_at_risk - (1 / (1 - cvar.confidence_level)) * expected_shortfall
    )
    return cvar_expr


def build_objective(milp_model: EnergyMILPModel, objective: Objective) -> linopy.LinearExpression:
    """Build the full objective: Σ weight_i * term_i(model)."""
    expr = objective.profit.weight * _profit_expr(milp_model)
    if objective.cvar is not None:
        expr = expr + objective.cvar.weight * _cvar_expr(milp_model, objective.cvar)
    return expr
