"""HiGHS solver implementation for energy system optimization.

This module provides the HiGHSolver class for solving energy system
optimization problems using the HiGHS linear programming solver.
"""

from typing import TYPE_CHECKING, cast

import pyomo.environ as pyo

from optimes._math_model.algebraic_model import AlgebraicModel
from optimes.optimization.optimization_results import OptimizationResults

if TYPE_CHECKING:
    from pyomo.opt import SolverResults


def optimize_algebraic_model(model: AlgebraicModel, *args: object, **kwargs: object) -> OptimizationResults:
    """Solve the optimization model using HiGHS.

    Args:
        model: The algebraic model to solve.
        *args: Additional positional arguments for the solver.
        **kwargs: Additional keyword arguments for the solver.

    Returns:
        OptimizationResults containing the solution and metadata.

    """
    solver = pyo.SolverFactory("highs")
    solver_results = solver.solve(
        model.pyomo_model,
        *args,
        **kwargs,
    )
    solver_results = cast("SolverResults", solver_results)
    return OptimizationResults(pyomo_solver_results=solver_results, algebraic_model=model)
