"""HiGHS solver implementation for energy system optimization.

This module provides the HiGHSolver class for solving energy system
optimization problems using the HiGHS linear programming solver.
"""

from linopy.constants import SolverStatus, TerminationCondition

from odys.math_model.milp_model import EnergyMILPModel
from odys.optimization.optimization_results import OptimizationResults
from odys.solvers.solver_config import SolverConfig


def optimize_algebraic_model(
    milp_model: EnergyMILPModel,
    solver_config: SolverConfig | None = None,
) -> OptimizationResults:
    """Solve the optimization model using HiGHS.

    Args:
        milp_model: The EnergyMILPModel to solve.
        solver_config: Solver configuration. Uses defaults if not provided.

    Returns:
        OptimizationResults containing the solution and metadata.

    """
    config = solver_config or SolverConfig()
    solving_status, termination_condition = milp_model.linopy_model.solve(
        solver_name="highs",
        explicit_coordinate_names=True,
        **config.to_solver_options(),
    )

    return OptimizationResults(
        solver_status=SolverStatus(solving_status),
        termination_condition=TerminationCondition(termination_condition),
        milp_model=milp_model,
    )
