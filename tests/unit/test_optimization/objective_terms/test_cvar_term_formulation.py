"""Unit tests for the CVaR objective term: variables, shortfall constraint and expression."""

from collections.abc import Callable

import linopy
import numpy as np
import pytest
from linopy.testing import assert_conequal, assert_linequal

from odys.domain.exceptions import OdysError
from odys.domain.objective import CVaRTerm, Objective, ProfitTerm
from odys.optimization.formulations.base import per_scenario_profit
from odys.optimization.model.model_builder import build_model
from odys.optimization.objective_terms.base import ObjectiveTermInputs
from odys.optimization.objective_terms.cvar import CVaRTermFormulation
from odys.optimization.problem import OptimizationProblem
from odys.parameters.dimensions import ModelDimension

CVAR_WEIGHT = 0.3
CONFIDENCE_LEVEL = 0.9
PROFIT_TERM = ProfitTerm(weight=0.7)
CVAR_TERM = CVaRTerm(weight=CVAR_WEIGHT, confidence_level=CONFIDENCE_LEVEL)
CVAR_OBJECTIVE = Objective(terms=(PROFIT_TERM, CVAR_TERM))
SCENARIOS = ModelDimension.Scenarios

ProblemWith = Callable[[Objective], OptimizationProblem]


def _cvar_term(problem: OptimizationProblem) -> CVaRTermFormulation:
    term = next((term for term in problem.objective_terms if isinstance(term, CVaRTermFormulation)), None)
    assert term is not None
    return term


@pytest.fixture
def problem(problem_with: ProblemWith) -> OptimizationProblem:
    return problem_with(CVAR_OBJECTIVE)


@pytest.fixture
def linopy_model(problem: OptimizationProblem) -> linopy.Model:
    return build_model(problem)


def test_cvar_term_build_returns_none_without_a_cvar_term(problem_with: ProblemWith) -> None:
    problem = problem_with(Objective())
    inputs = ObjectiveTermInputs(objective=Objective(), context=problem.context, formulations=problem.formulations)

    assert CVaRTermFormulation.build(inputs) is None


def test_cvar_value_at_risk_is_one_free_variable(linopy_model: linopy.Model) -> None:
    value_at_risk = linopy_model.variables[CVaRTermFormulation.value_at_risk_name]

    assert value_at_risk.dims == ()
    assert float(value_at_risk.lower) == -np.inf


def test_cvar_shortfall_is_non_negative_per_scenario(
    problem: OptimizationProblem,
    linopy_model: linopy.Model,
) -> None:
    shortfall = linopy_model.variables[CVaRTermFormulation.shortfall_name]

    assert shortfall.dims == (SCENARIOS.value,)
    assert list(shortfall.coords[SCENARIOS.value].values) == list(problem.context.scenarios.labels)
    assert bool((shortfall.lower == 0).all())


def test_cvar_shortfall_constraint_is_value_at_risk_minus_scenario_profit(
    problem: OptimizationProblem,
    linopy_model: linopy.Model,
) -> None:
    variables = _cvar_term(problem).variables
    actual = linopy_model.constraints["cvar_shortfall_constraint"]

    expected = variables.shortfall >= variables.value_at_risk - per_scenario_profit(problem.formulations)

    assert_conequal(expected, actual.lhs >= actual.rhs)
    assert bool((actual.labels != -1).all())


@pytest.mark.usefixtures("linopy_model")
def test_cvar_expression_is_weighted_value_at_risk_less_tail_shortfall(problem: OptimizationProblem) -> None:
    variables = _cvar_term(problem).variables
    expected_shortfall = (problem.context.probabilities * variables.shortfall).sum(SCENARIOS)

    expected = CVAR_WEIGHT * (variables.value_at_risk - (1 / (1 - CONFIDENCE_LEVEL)) * expected_shortfall)

    assert_linequal(_cvar_term(problem).expression(), expected)


def test_cvar_variables_raise_before_they_are_added(problem: OptimizationProblem) -> None:
    with pytest.raises(OdysError, match="add_variables must run before its variables are used"):
        _ = _cvar_term(problem).variables


@pytest.mark.usefixtures("linopy_model")
def test_cvar_term_belongs_to_one_model_only(problem: OptimizationProblem) -> None:
    with pytest.raises(OdysError, match="already has variables; build a new problem for each model"):
        _cvar_term(problem).add_variables(linopy.Model())


@pytest.mark.parametrize(
    "terms",
    [(PROFIT_TERM, CVAR_TERM), (CVAR_TERM, PROFIT_TERM)],
    ids=["profit_first", "cvar_first"],
)
def test_model_objective_is_the_profit_term_plus_the_cvar_term(
    problem_with: ProblemWith,
    terms: tuple[ProfitTerm | CVaRTerm, ...],
) -> None:
    problem = problem_with(Objective(terms=terms))
    model = build_model(problem)
    profit_term, cvar_term = problem.objective_terms

    assert model.objective.sense == "max"
    assert_linequal(model.objective.expression, profit_term.expression() + cvar_term.expression())
