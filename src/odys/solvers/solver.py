"""Solver dispatch for energy system optimization.

This module provides the solve function that dispatches to any
linopy-supported solver based on the SolverConfig.
"""

import linopy
from linopy.constants import SolverStatus, TerminationCondition

from odys.domain.exceptions import OdysSolverError
from odys.optimization.model.milp_model import EnergyMILPModel
from odys.results.optimization_results import OptimalDisptachResults
from odys.solvers.config_translators import translate_solver_config
from odys.solvers.solver_config import SolverConfig, SolverName


def optimize_algebraic_model(
    milp_model: EnergyMILPModel,
    solver_config: SolverConfig | None = None,
) -> OptimalDisptachResults:
    """Solve the optimization model using the configured solver.

    Args:
        milp_model: The EnergyMILPModel to solve.
        solver_config: Solver configuration. Uses defaults (HiGHS) if not provided.

    Returns:
        OptimizationResults containing the solution and metadata.

    Raises:
        OdysSolverError: If the configured solver is not available.

    """
    config = solver_config or SolverConfig()
    validate_solver_available(config.solver_name)

    solver_status, termination_condition = milp_model.linopy_model.solve(
        solver_name=config.solver_name,
        explicit_coordinate_names=True,
        **translate_solver_config(config),
    )

    return OptimalDisptachResults(
        solver_status=SolverStatus(solver_status),
        termination_condition=TerminationCondition(termination_condition),
        solution=milp_model.linopy_model.solution,
        objective_value=milp_model.linopy_model.objective.value,
    )


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
