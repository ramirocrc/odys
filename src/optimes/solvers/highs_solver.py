"""HiGHS solver implementation for energy system optimization.

This module provides the HiGHSolver class for solving energy system
optimization problems using the HiGHS linear programming solver.
"""

from typing import TYPE_CHECKING, cast

import pyomo.environ as pyo
from pyomo.contrib.solver.solvers.highs import NoFeasibleSolutionError
from pyomo.util.infeasible import log_infeasible_constraints

from optimes._math_model.algebraic_model import AlgebraicModel
from optimes.optimization.optimization_results import OptimizationResults
from optimes.utils.logging import get_logger

if TYPE_CHECKING:
    from pyomo.opt import SolverResults

logger = get_logger(__name__)


def optimize_algebraic_model(model: AlgebraicModel, **kwargs: object) -> OptimizationResults:
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
        model=model.pyomo_model,
        load_solutions=False,
        **kwargs,
    )
    solver_results = cast("SolverResults", solver_results)

    if solver_results.solver.termination_condition == pyo.TerminationCondition.infeasible:
        logger.info("Logging infeasible constraints")
        log_infeasible_constraints(
            model.pyomo_model,
            logger=logger,
            log_expression=True,
            log_variables=True,
        )
        raise NoFeasibleSolutionError

    model.pyomo_model.solutions.load_from(solver_results)
    return OptimizationResults(pyomo_solver_results=solver_results, algebraic_model=model)
