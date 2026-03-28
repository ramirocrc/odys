"""Solver dispatch for energy system optimization.

This module provides the solve function that dispatches to any
linopy-supported solver based on the SolverConfig.
"""

import linopy
from linopy.constants import SolverStatus, TerminationCondition

from odys.exceptions import OdysSolverError
from odys.math_model.milp_model import EnergyMILPModel
from odys.optimization.optimization_results import OptimizationResults
from odys.optimization.solved_model_data import SolvedModelData
from odys.solvers.solver_config import SolverConfig


def optimize_algebraic_model(
    milp_model: EnergyMILPModel,
    solver_config: SolverConfig | None = None,
) -> OptimizationResults:
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
    _validate_solver_available(config.solver_name)

    solving_status, termination_condition = milp_model.linopy_model.solve(
        solver_name=config.solver_name,
        explicit_coordinate_names=True,
        **config.to_solver_options(),
    )

    cvar_term = milp_model.parameters.objective.cvar
    solved_data = SolvedModelData(
        solution=milp_model.linopy_model.solution,
        variable_names=frozenset(milp_model.linopy_model.variables.labels),
        has_generators=milp_model.parameters.generators is not None,
        has_storages=milp_model.parameters.storages is not None,
        has_markets=milp_model.parameters.markets is not None,
        cvar_term=cvar_term,
        scenario_probabilities=(
            milp_model.parameters.scenarios.scenario_probabilities.to_series() if cvar_term is not None else None
        ),
    )

    return OptimizationResults(
        solver_status=SolverStatus(solving_status),
        termination_condition=TerminationCondition(termination_condition),
        solved_data=solved_data,
    )


def _validate_solver_available(solver_name: str) -> None:
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
