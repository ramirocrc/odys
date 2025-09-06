"""Optimization results handling for energy system models.

This module provides classes for handling and analyzing optimization results
from energy system models.
"""

import pandas as pd
from linopy import Model
from linopy.constants import SolverStatus, TerminationCondition

from optimes._math_model.model_components.variables import ModelVariable
from optimes.optimization.result_containers import BatteryResults, GeneratorResults


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

        Returns:
            DataFrame containing all solution variables with units, variables,
            and time periods as multi-level index columns.
        """
        if self._solver_status != SolverStatus.ok:
            msg = f"No solution available. Optimization Termination Condition: {self.termination_condition}."
            raise ValueError(msg)

        ds = self._linopy_model.solution
        dfs = []
        for variable in ModelVariable:
            variable_name = variable.var_name
            df = ds[variable_name].to_series().reset_index()
            df = df.rename(columns={variable.asset_dimension.value: "unit", variable_name: "value"})
            df = df[["unit", "time", "value"]]
            df["variable"] = variable_name
            dfs.append(df)

        df_final = pd.concat(dfs, ignore_index=True)
        df_final = df_final[["unit", "variable", "time", "value"]]
        return df_final.set_index(["unit", "variable", "time"]).sort_index()

    @property
    def batteries(self) -> BatteryResults:
        """Get battery results."""
        return BatteryResults(
            net_power=self._get_variable_results(ModelVariable.BATTERY_POWER_NET),
            state_of_charge=self._get_variable_results(ModelVariable.BATTERY_SOC),
        )

    @property
    def generators(self) -> GeneratorResults:
        """Get generator results."""
        return GeneratorResults(
            power=self._get_variable_results(ModelVariable.GENERATOR_POWER),
            status=self._get_variable_results(ModelVariable.GENERATOR_STATUS),
        )

    def _get_variable_results(self, variable: ModelVariable) -> pd.DataFrame:
        return self._linopy_model.solution[variable.var_name].to_series().unstack()  # noqa: PD010
