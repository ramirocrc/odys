"""Unit tests for the expected-profit objective term."""

from collections.abc import Callable
from typing import get_args

import pytest
from linopy.testing import assert_linequal

from odys.domain.objective import CVaRTerm, Objective, ProfitTerm
from odys.optimization.formulations.base import per_scenario_profit
from odys.optimization.model.model_builder import build_model
from odys.optimization.objective_terms import OBJECTIVE_TERM_FORMULATIONS
from odys.optimization.objective_terms.cvar import CVaRTermFormulation
from odys.optimization.objective_terms.profit import ProfitTermFormulation
from odys.optimization.problem import OptimizationProblem
from odys.parameters.dimensions import ModelDimension

PROFIT_WEIGHT = 0.7
CVAR_TERM = CVaRTerm(weight=0.3, confidence_level=0.9)
ONE_OF_EACH_TERM = {ProfitTerm: ProfitTerm(weight=PROFIT_WEIGHT), CVaRTerm: CVAR_TERM}

ProblemWith = Callable[[Objective], OptimizationProblem]


def _profit_term(problem: OptimizationProblem) -> ProfitTermFormulation:
    term = next((term for term in problem.objective_terms if isinstance(term, ProfitTermFormulation)), None)
    assert term is not None
    return term


def test_objective_term_formulations_are_profit_then_cvar() -> None:
    assert (ProfitTermFormulation, CVaRTermFormulation) == OBJECTIVE_TERM_FORMULATIONS


def test_every_objective_term_type_has_a_formulation(problem_with: ProblemWith) -> None:
    term_union, _ = get_args(Objective.model_fields["terms"].annotation)
    assert set(ONE_OF_EACH_TERM) == set(get_args(term_union))

    problem = problem_with(Objective(terms=tuple(ONE_OF_EACH_TERM.values())))

    assert len(problem.objective_terms) == len(ONE_OF_EACH_TERM)


@pytest.mark.parametrize("weight", [PROFIT_WEIGHT, 0.0], ids=["weighted", "zero_weight"])
def test_profit_term_expression_is_weighted_expected_profit(problem_with: ProblemWith, weight: float) -> None:
    problem = problem_with(Objective(terms=(ProfitTerm(weight=weight),)))
    build_model(problem)

    profit = per_scenario_profit(problem.formulations)
    expected_profit = (profit * problem.context.probabilities).sum(ModelDimension.Scenarios)

    assert_linequal(_profit_term(problem).expression(), weight * expected_profit)
