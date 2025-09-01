"""HiGHS solver implementation for energy system optimization.

This module provides the HiGHSolver class for solving energy system
optimization problems using the HiGHS linear programming solver.
"""

from linopy import Model

from optimes.optimization.optimization_results import OptimizationResults
from optimes.utils.logging import get_logger

logger = get_logger(__name__)


def optimize_algebraic_model(linopy_model: Model) -> OptimizationResults:
    """Solve the optimization model using HiGHS.

    Args:
        linopy_model: The linopy model to solve.

    Returns:
        OptimizationResults containing the solution and metadata.

    """
    solving_status, termination_condition = linopy_model.solve(solver_name="highs")
    linopy_model.to_file("linear_model.lp", explicit_coordinate_names=True)

    return OptimizationResults(
        solving_status=solving_status,
        termination_condition=termination_condition,
        linopy_model=linopy_model,
    )
