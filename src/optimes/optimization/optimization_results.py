"""Optimization results handling for energy system models.

This module provides classes for handling and analyzing optimization results
from energy system models.
"""

from typing import cast

import pandas as pd
from pyomo.opt import SolverResults, SolverStatus, TerminationCondition

from optimes._math_model.algebraic_model import AlgebraicModel


class OptimizationResults:
    """Container for optimization results and metadata.

    This class wraps the solver results and provides convenient access
    to solution data, solver status, and termination conditions.
    """

    def __init__(
        self,
        pyomo_solver_results: SolverResults,
        algebraic_model: AlgebraicModel,
    ) -> None:
        """Initialize optimization results.

        Args:
            pyomo_solver_results: The raw solver results from Pyomo.
            algebraic_model: The algebraic model that was solved.

        Raises:
            TypeError: If arguments are not of the expected types.

        """
        if not isinstance(pyomo_solver_results, SolverResults):
            msg = f"Expected pyomo_solver_results to be of type SolverResults, got {type(pyomo_solver_results)}"
            raise TypeError(msg)

        if not isinstance(algebraic_model, AlgebraicModel):
            msg = f"Expected pyomo_model to be of type AlgebraicModel, got {type(pyomo_solver_results)}"
            raise TypeError(msg)

        self._pyomo_solver_results = pyomo_solver_results
        self._algebraic_model = algebraic_model

    @property
    def algebraic_model(self) -> AlgebraicModel:
        """Get the algebraic model that was solved.

        Returns:
            The algebraic model instance.

        """
        return self._algebraic_model

    @property
    def solving_status(self) -> SolverStatus:
        """Get the solver status.

        Returns:
            The solver status indicating whether the solve was successful.

        """
        status = self._pyomo_solver_results.solver.status
        return cast("SolverStatus", status)

    @property
    def termination_condition(self) -> TerminationCondition:
        """Get the termination condition.

        Returns:
            The termination condition indicating how the solver finished.

        """
        termination_condition = self._pyomo_solver_results.solver.termination_condition
        return cast("TerminationCondition", termination_condition)

    @property
    def to_dataframe(self) -> pd.DataFrame:
        """Convert optimization results to a pandas DataFrame.

        Returns:
            DataFrame containing the solution variables with time periods
            as rows and variables as columns.

        """
        return self.algebraic_model.to_dataframe
