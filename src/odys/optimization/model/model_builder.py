"""Builds the linopy model of an optimization problem: variables, constraints and objective."""

from functools import reduce
from operator import add

import linopy

from odys.optimization.power_balance import PowerBalance
from odys.optimization.problem import OptimizationProblem


def build_model(problem: OptimizationProblem) -> linopy.Model:
    """Build the optimization model of an energy system.

    Variables come first (entity formulations, then objective terms), then
    constraints (entity formulations, the power balance, objective terms), then
    the objective: the sum of the weighted terms, maximized. A problem is built
    into one model only; its formulations refuse a second `add_variables`.

    Args:
        problem: The formulations of the energy system and of its objective terms.

    Returns:
        The linopy model, ready for solving.

    """
    model = linopy.Model(force_dim_names=True)
    for formulation in problem.formulations:
        formulation.add_variables(model)
    for term in problem.objective_terms:
        term.add_variables(model)

    for formulation in problem.formulations:
        formulation.add_to_model(model)
    PowerBalance(problem.formulations).add_to_model(model)
    for term in problem.objective_terms:
        term.add_to_model(model)

    objective: linopy.LinearExpression = reduce(add, (term.expression() for term in problem.objective_terms))
    model.add_objective(objective, sense="max")
    return model
