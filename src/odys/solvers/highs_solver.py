"""HiGHS solver implementation for energy system optimization.

This module provides the HiGHSolver class for solving energy system
optimization problems using the HiGHS linear programming solver.
"""

from linopy.constants import SolverStatus, TerminationCondition

from odys._math_model.milp_model import EnergyMILPModel
from odys.optimization.optimization_results import OptimizationResults


def optimize_algebraic_model(milp_model: EnergyMILPModel) -> OptimizationResults:
    """Solve the optimization model using HiGHS.

    Args:
        milp_model: The EnergyMILPModel to solve.

    Returns:
        OptimizationResults containing the solution and metadata.

    """
    solving_status, termination_condition = milp_model.linopy_model.solve(
        solver_name="highs",
        explicit_coordinate_names=True,
    )

    return OptimizationResults(
        solver_status=SolverStatus(solving_status),
        termination_condition=TerminationCondition(termination_condition),
        milp_model=milp_model,
    )
