"""Solver dispatch for energy system optimization.

This module provides the solve function that dispatches to any
linopy-supported solver based on the SolverConfig.
"""

import linopy
import xarray as xr

from odys.domain.exceptions import OdysSolverError
from odys.solvers.config_translators import translate_solver_config
from odys.solvers.outcome import SolveOutcome, SolveStatus
from odys.solvers.solver_config import SolverConfig, SolverName


def solve(model: linopy.Model, solver_config: SolverConfig) -> SolveOutcome:
    """Solve the model with the configured solver.

    Args:
        model: The linopy model to solve.
        solver_config: Solver configuration.

    Returns:
        The solver status, termination condition, objective value and solution. Without a solution
        (a status other than `OK`, or `OK` with no solution, such as a time limit before the first
        feasible solution) the objective value is `None` and the solution is empty.

    Raises:
        OdysSolverError: If the configured solver is not available.

    """
    validate_solver_available(solver_config.solver_name)

    status, termination_condition = model.solve(
        solver_name=solver_config.solver_name,
        explicit_coordinate_names=True,
        **translate_solver_config(solver_config),
    )

    solve_status = SolveStatus(status)
    solution = _solution_of(model) if solve_status is SolveStatus.OK else None
    if solution is None:
        return SolveOutcome(
            status=solve_status,
            termination_condition=termination_condition,
            objective_value=None,
            solution=xr.Dataset(),
        )
    return SolveOutcome(
        status=solve_status,
        termination_condition=termination_condition,
        objective_value=model.objective.value,
        solution=solution,
    )


def _solution_of(model: linopy.Model) -> xr.Dataset | None:
    """Return the solution of a solved model, or `None` when the solver set none (linopy then raises)."""
    try:
        return model.solution
    except AttributeError:
        return None


def validate_solver_available(solver_name: SolverName) -> None:
    """Validate that the solver is installed and available.

    Args:
        solver_name: The solver name to check.

    Raises:
        OdysSolverError: If the solver is not in linopy.available_solvers.

    """
    if solver_name not in linopy.available_solvers:
        available = ", ".join(sorted(linopy.available_solvers)) or "none"
        msg = f"Solver '{solver_name}' is not available. Installed solvers: {available}."
        raise OdysSolverError(msg)
