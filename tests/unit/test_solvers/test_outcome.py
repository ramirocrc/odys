"""Tests for the solve outcome, which results read instead of linopy."""

import pytest
import xarray as xr

from odys.solvers.outcome import SolveOutcome, SolveStatus

ZERO_OBJECTIVE = 0.0


@pytest.mark.parametrize(
    ("objective_value", "expected"),
    [(ZERO_OBJECTIVE, True), (None, False)],
    ids=["zero-objective-is-a-solution", "no-objective-is-no-solution"],
)
def test_outcome_has_solution_depends_only_on_the_objective_being_set(
    objective_value: float | None,
    *,
    expected: bool,
) -> None:
    outcome = SolveOutcome(
        status=SolveStatus.OK,
        termination_condition="optimal",
        objective_value=objective_value,
        solution=xr.Dataset(),
    )

    assert outcome.has_solution is expected
