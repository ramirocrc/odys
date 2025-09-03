"""Optimization results handling for energy system models.

This module provides classes for handling and analyzing optimization results
from energy system models.
"""

import pandas as pd
from linopy import Model
from linopy.constants import SolverStatus, TerminationCondition


class OptimizationResults:
    """Container for optimization results and metadata.

    This class wraps the solver results and provides convenient access
    to solution data, solver status, and termination conditions.
    """

    def __init__(
        self,
        solver_status: SolverStatus,
        termination_condition: TerminationCondition,
        linopy_model: Model,
    ) -> None:
        """Initialize the optimization results object.

        Args:
            solver_status: Solving status
            termination_condition: Termination condition
            linopy_model: Solved Linopy Model
        """
        self._solver_status = solver_status
        self._termination_condition = termination_condition
        self._linopy_model = linopy_model

    @property
    def solver_status(self) -> str:
        """Get the solver status.

        Returns:
            The solver status indicating whether the solve was successful.

        """
        return self._solver_status.value

    @property
    def termination_condition(self) -> str:
        """Get the termination condition.

        Returns:
            The termination condition indicating how the solver finished.

        """
        return self._termination_condition.value

    def to_dataframe(self) -> pd.DataFrame:
        """Convert optimization results to a pandas DataFrame.

        Args:
            detail: Specifies the level of detail to include in the dataframe. A "basic" dataframe will output the main
            decision variable for each asset. A "detailed" dataframe will output all decision variables.

        Returns:
            DataFrame containing the solution variables with time periods
            as rows and variables as columns.
        """
        if self._solver_status != SolverStatus.ok:
            msg = f"No solution available. Optimization Termination Condition: {self.termination_condition}."
            raise ValueError(msg)
        return self._get_detailed_dataframe()

    def _get_detailed_dataframe(self) -> pd.DataFrame:
        ds = self._linopy_model.solution
        dfs = []
        for var in [v for v in ds.data_vars if str(v).startswith("generator")]:
            df = ds[var].to_dataframe().reset_index()
            df = df.rename(columns={"generators": "unit", var: "value"})
            df = df[["unit", "time", "value"]]
            df["variable"] = var
            dfs.append(df)

        # battery variables
        for var in [v for v in ds.data_vars if str(v).startswith("battery")]:
            df = ds[var].to_dataframe().reset_index()
            df = df.rename(columns={"batteries": "unit", var: "value"})
            df = df[["unit", "time", "value"]]
            df["variable"] = var
            dfs.append(df)

        # combine everything
        df_final = pd.concat(dfs, ignore_index=True)

        # reorder and set index
        df_final = df_final[["unit", "variable", "time", "value"]]
        return df_final.set_index(["unit", "variable", "time"]).sort_index()
