"""Tests for the solver module."""

from typing import cast

import linopy
import pytest
from linopy.constants import SolverStatus

from odys.domain.exceptions import OdysSolverError
from odys.solvers.outcome import SolveStatus
from odys.solvers.solver import solve, validate_solver_available
from odys.solvers.solver_config import SolverConfig, SolverName

UPPER_BOUND = 4.0
VARIABLE_NAME = "x"


def _bounded_model(lower: float) -> linopy.Model:
    model = linopy.Model()
    x = model.add_variables(lower=lower, upper=UPPER_BOUND, name=VARIABLE_NAME)
    model.add_objective(1 * x, sense="max")
    return model


def test_validate_solver_available_highs() -> None:
    """HiGHS is installed and passes validation."""
    validate_solver_available(SolverName.HIGHS)


def test_validate_solver_unavailable_raises() -> None:
    """An unavailable solver raises OdysSolverError."""
    with pytest.raises(OdysSolverError, match="not available"):
        validate_solver_available(cast("SolverName", "nonexistent_solver"))


def test_solve_returns_the_outcome_of_a_feasible_model() -> None:
    outcome = solve(_bounded_model(lower=0.0), SolverConfig())

    assert outcome.status is SolveStatus.OK
    assert outcome.has_solution
    assert outcome.termination_condition == "optimal"
    assert outcome.objective_value == pytest.approx(UPPER_BOUND)
    assert float(outcome.solution[VARIABLE_NAME]) == pytest.approx(UPPER_BOUND)


def test_solve_reports_an_infeasible_model_without_a_solution() -> None:
    outcome = solve(_bounded_model(lower=UPPER_BOUND + 1), SolverConfig())

    assert outcome.status is SolveStatus.WARNING
    assert outcome.termination_condition == "infeasible"
    assert not outcome.has_solution
    assert outcome.objective_value is None
    assert not outcome.solution.data_vars


def test_solve_with_ok_status_but_no_solution_has_no_solution(monkeypatch: pytest.MonkeyPatch) -> None:
    """A time limit before the first incumbent (simulated; see the mocking exception in tests/CLAUDE.md)."""

    def stop_at_time_limit_without_incumbent(*_args: object, **_kwargs: object) -> tuple[str, str]:
        return SolveStatus.OK.value, "time_limit"

    monkeypatch.setattr(linopy.Model, "solve", stop_at_time_limit_without_incumbent)

    outcome = solve(_bounded_model(lower=0.0), SolverConfig())

    assert outcome.status is SolveStatus.OK
    assert not outcome.has_solution
    assert outcome.objective_value is None
    assert not outcome.solution.data_vars


def test_solve_with_an_unavailable_solver_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    """No solver is installed (simulated; see the mocking exception in tests/CLAUDE.md)."""
    monkeypatch.setattr(linopy, "available_solvers", [])
    with pytest.raises(OdysSolverError, match="not available"):
        solve(_bounded_model(lower=0.0), SolverConfig())


def test_solve_status_has_one_member_per_linopy_solver_status() -> None:
    assert {status.value for status in SolverStatus} == {status.value for status in SolveStatus}
