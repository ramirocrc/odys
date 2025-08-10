"""Optimization results handling for energy system models.

This module provides classes for handling and analyzing optimization results
from energy system models.
"""

from typing import cast

import pandas as pd
from pydantic import BaseModel
from pyomo.opt import SolverResults, SolverStatus, TerminationCondition

from optimes._math_model.algebraic_model import AlgebraicModel


class OptimizationResults(BaseModel, arbitrary_types_allowed=True, frozen=True):
    """Container for optimization results and metadata.

    This class wraps the solver results and provides convenient access
    to solution data, solver status, and termination conditions.
    """

    pyomo_solver_results: SolverResults
    algebraic_model: AlgebraicModel

    @property
    def solving_status(self) -> SolverStatus:
        """Get the solver status.

        Returns:
            The solver status indicating whether the solve was successful.

        """
        status = self.pyomo_solver_results.solver.status
        return cast("SolverStatus", status)

    @property
    def termination_condition(self) -> TerminationCondition:
        """Get the termination condition.

        Returns:
            The termination condition indicating how the solver finished.

        """
        termination_condition = self.pyomo_solver_results.solver.termination_condition
        return cast("TerminationCondition", termination_condition)

    def to_dataframe(self, direction: str = "vertical") -> pd.DataFrame:
        """Convert optimization results to a pandas DataFrame.

        Returns:
            DataFrame containing the solution variables with time periods
            as rows and variables as columns.

        """
        return self.algebraic_model.to_dataframe(direction)
