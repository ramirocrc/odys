"""HiGHS solver implementation for energy system optimization.

This module provides the HiGHSolver class for solving energy system
optimization problems using the HiGHS linear programming solver.
"""

from typing import TYPE_CHECKING, cast

import pyomo.environ as pyo

from optimes._math_model.algebraic_model import AlgebraicModel
from optimes.optimization.optimization_results import OptimizationResults
from optimes.solvers.base_solver import AlgebraicModelSolver

if TYPE_CHECKING:
    from pyomo.opt import SolverResults


class HiGHSolver(AlgebraicModelSolver):
    """HiGHS solver implementation for energy system optimization.

    This class provides an interface to the HiGHS solver for solving
    linear programming problems in energy system optimization.
    """

    def __init__(self) -> None:
        """Initialize the HiGHS solver with Pyomo solver factory."""
        self._solver = pyo.SolverFactory("highs")

    def solve(self, model: AlgebraicModel, *args: object, **kwargs: object) -> OptimizationResults:
        """Solve the optimization model using HiGHS.

        Args:
            model: The algebraic model to solve.
            *args: Additional positional arguments for the solver.
            **kwargs: Additional keyword arguments for the solver.

        Returns:
            OptimizationResults containing the solution and metadata.

        """
        solver_results = self._solver.solve(
            model.pyomo_model,
            *args,
            **kwargs,
        )
        solver_results = cast("SolverResults", solver_results)
        return OptimizationResults(pyomo_solver_results=solver_results, algebraic_model=model)
