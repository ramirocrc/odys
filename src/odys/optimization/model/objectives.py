"""Objective function definitions for energy system optimization models."""

from functools import reduce
from operator import add
from typing import assert_never

import linopy

from odys.domain.objective import CVaRTerm, Objective, ProfitTerm
from odys.optimization.model.milp_model import EnergyMILPModel
from odys.parameters.dimensions import ModelDimension


def _profit_expr(model: EnergyMILPModel) -> linopy.LinearExpression:
    probs = model.parameters.context.probabilities
    return (model.problem.per_scenario_profit() * probs).sum(ModelDimension.Scenarios)


def _cvar_expr(model: EnergyMILPModel, cvar: CVaRTerm) -> linopy.LinearExpression:
    probs = model.parameters.context.probabilities
    expected_shortfall = (probs * model.vars.cvar_shortfall).sum(ModelDimension.Scenarios)
    cvar_expr: linopy.LinearExpression = (
        model.vars.cvar_value_at_risk - (1 / (1 - cvar.confidence_level)) * expected_shortfall
    )
    return cvar_expr


def _term_expr(model: EnergyMILPModel, term: ProfitTerm | CVaRTerm) -> linopy.LinearExpression:
    match term:
        case ProfitTerm():
            return _profit_expr(model)
        case CVaRTerm():
            return _cvar_expr(model, term)
        case _:
            assert_never(term)


def build_objective(milp_model: EnergyMILPModel, objective: Objective) -> linopy.LinearExpression:
    """Build the full objective: Σ weight_i * term_i(model).

    Args:
        milp_model: The model whose variables the terms are built from.
        objective: The objective terms; never empty, since a `ProfitTerm` is required.

    Returns:
        The weighted sum of the terms, to maximize.
    """
    weighted_terms = [term.weight * _term_expr(milp_model, term) for term in objective.terms]
    return reduce(add, weighted_terms)
