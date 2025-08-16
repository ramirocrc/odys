"""Optimization results handling for energy system models.

This module provides classes for handling and analyzing optimization results
from energy system models.
"""

from enum import Enum
from typing import TYPE_CHECKING, cast

import pandas as pd
import pyomo.environ as pyo
from pyomo.opt import SolverResults, SolverStatus, TerminationCondition

from optimes._math_model.algebraic_model import AlgebraicModel
from optimes._math_model.model_components.sets import EnergyModelSetName

if TYPE_CHECKING:
    from pyomo.core.base.var import IndexedVar


class ResultDfDetail(Enum):
    """Level of detail of results dataframe."""

    BASIC = "basic"
    DETAILED = "detailed"


class OptimizationResults:
    """Container for optimization results and metadata.

    This class wraps the solver results and provides convenient access
    to solution data, solver status, and termination conditions.
    """

    def __init__(self, pyomo_solver_results: SolverResults, algebraic_model: AlgebraicModel) -> None:
        """Initialize the optimization results object.

        Args:
            pyomo_solver_results: pyomo solver results
            algebraic_model: Solved AlgebraicModel
        """
        self._pyomo_solver_results = pyomo_solver_results
        self._algebraic_model = algebraic_model

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

    def to_dataframe(self, detail: str) -> pd.DataFrame:
        """Convert optimization results to a pandas DataFrame.

        Args:
            detail: Specifies the level of detail to include in the dataframe. A "basic" dataframe will output the main
            decision variable for each asset. A "detailed" dataframe will output all decision variables.

        Returns:
            DataFrame containing the solution variables with time periods
            as rows and variables as columns.
        """
        if ResultDfDetail(detail) == ResultDfDetail.BASIC:
            return self._get_basic_dataframe()
        return self._get_detailed_dataframe()

    def _get_basic_dataframe(self) -> pd.DataFrame:
        results = pd.DataFrame()
        for asset_set in [EnergyModelSetName.BATTERIES, EnergyModelSetName.GENERATORS]:
            linked_independent_variable = self._algebraic_model.get_var(asset_set.independent_variable)
            linked_independent_variable = cast("IndexedVar", linked_independent_variable)
            first_index_set, _ = linked_independent_variable.index_set().subsets()
            if first_index_set.name != "time":
                msg = f"Expected first index set of variable to be 'time', got {first_index_set.name} instead"
                raise ValueError(msg)

            for idx in linked_independent_variable:
                if idx is None:
                    msg = "Index cannot be None"
                    raise ValueError(msg)
                time, unit = idx
                results.loc[time, unit] = linked_independent_variable[(time, unit)].value
        results.index.name = "time"
        return results

    def _get_detailed_dataframe(self) -> pd.DataFrame:
        aggregated_variables_data = {}
        for variable in self._algebraic_model.pyomo_model.component_objects(pyo.Var, active=True):
            variable = cast("IndexedVar", variable)
            first_index_set, _ = variable.index_set().subsets()
            if first_index_set.name != "time":
                msg = f"Expected first index set of variable to be 'time', got {first_index_set.name} instead"
                raise ValueError(msg)
            var_name = variable.name
            data = []
            for idx in variable:
                if idx is None:
                    msg = "Index cannot be None"
                    raise ValueError(msg)
                time, unit = idx
                val = variable[idx].value
                data.append((time, unit, val))

            variable_data = pd.DataFrame(data, columns=["time", "unit", "value"])  # pyright: ignore reportArgumentType
            aggregated_variables_data[var_name] = variable_data.pivot_table(
                index="time",
                columns="unit",
                values="value",
            )
        return pd.concat(aggregated_variables_data, axis=1)
