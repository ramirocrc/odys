"""Optimization results handling for energy system models.

This module provides classes for handling and analyzing optimization results
from energy system models.
"""

from functools import cached_property

import pandas as pd
import xarray as xr
from linopy.constants import SolverStatus, TerminationCondition

from odis._math_model.milp_model import EnergyMILPModel
from odis._math_model.model_components.sets import ModelDimension
from odis._math_model.model_components.variables import ModelVariable
from odis.optimization.result_containers import BatteryResults, GeneratorResults, MarketResults


class OptimizationResults:
    """Container for optimization results and metadata.

    This class wraps the solver results and provides convenient access
    to solution data, solver status, and termination conditions.
    """

    def __init__(
        self,
        solver_status: SolverStatus,
        termination_condition: TerminationCondition,
        milp_model: EnergyMILPModel,
    ) -> None:
        """Initialize the optimization results object.

        Args:
            solver_status: Solving status
            termination_condition: Termination condition
            milp_model: Solved EnergyMILPModel Model
        """
        self._solver_status = solver_status
        self._termination_condition = termination_condition
        self._milp_model = milp_model

    @cached_property
    def solver_status(self) -> str:
        """Get the solver status.

        Returns:
            The solver status indicating whether the solve was successful.

        """
        return self._solver_status.value

    @cached_property
    def termination_condition(self) -> str:
        """Get the termination condition.

        Returns:
            The termination condition indicating how the solver finished.

        """
        return self._termination_condition.value

    @cached_property
    def _solution(self) -> xr.Dataset:
        self._validate_terminated_successfully()
        return self._milp_model.linopy_model.solution

    @cached_property
    def to_dataframe(self) -> pd.DataFrame:
        """Convert optimization results to a pandas DataFrame.

        Returns:
            DataFrame containing all solution variables with units, variables,
            and time periods as multi-level index columns.
        """
        dfs = []
        for variable in ModelVariable:
            variable_name = variable.var_name
            # Skip if there is this variable is not populated (eg skip battery varialbes if no batteries in the system)
            if variable_name not in self._milp_model.linopy_model.variables.labels:
                continue
            var_solution = self._solution[variable_name]
            df = (
                var_solution.to_series()
                .reset_index()
                .rename(columns={variable.asset_dimension: "unit", variable_name: "value"})
                .assign(variable=variable_name)
            )
            dfs.append(df)

        return (
            pd.concat(dfs, ignore_index=True)
            .set_index([
                ModelDimension.Scenarios,
                "unit",
                "variable",
                ModelDimension.Time,
            ])
            .sort_index()
            .pipe(self._drop_single_scenario_level)
        )

    def _drop_single_scenario_level(self, df: pd.DataFrame) -> pd.DataFrame:
        scenario_values = df.index.get_level_values(ModelDimension.Scenarios).to_numpy()
        if (scenario_values == scenario_values[0]).all():
            return df.droplevel(ModelDimension.Scenarios)
        return df

    def _validate_terminated_successfully(self) -> None:
        if self._solver_status != SolverStatus.ok:
            msg = f"No solution available. Optimization Termination Condition: {self.termination_condition}."
            raise ValueError(msg)

    @cached_property
    def batteries(self) -> BatteryResults:
        """Get battery results."""
        self._validate_terminated_successfully()
        if self._milp_model.parameters.batteries is None:
            msg = "This model does not contain battery results"
            raise ValueError(msg)
        return BatteryResults(
            net_power=self._get_variable_results(ModelVariable.BATTERY_POWER_NET),
            state_of_charge=self._get_variable_results(ModelVariable.BATTERY_SOC),
        )

    @cached_property
    def markets(self) -> MarketResults:
        """Get battery results."""
        self._validate_terminated_successfully()
        if self._milp_model.parameters.markets is None:
            msg = "This model does not contain market results"
            raise ValueError(msg)
        return MarketResults(
            sell_volume=self._get_variable_results(ModelVariable.MARKET_SELL),
            buy_volume=self._get_variable_results(ModelVariable.MARKET_BUY),
        )

    @cached_property
    def generators(self) -> GeneratorResults:
        """Get generator results."""
        self._validate_terminated_successfully()
        if self._milp_model.parameters.generators is None:
            msg = "This model does not contain generator results"
            raise ValueError(msg)

        return GeneratorResults(
            power=self._get_variable_results(ModelVariable.GENERATOR_POWER),
            status=self._get_variable_results(ModelVariable.GENERATOR_STATUS),
            startup=self._get_variable_results(ModelVariable.GENERATOR_STARTUP),
            shutdown=self._get_variable_results(ModelVariable.GENERATOR_SHUTDOWN),
        )

    def _get_variable_results(self, variable: ModelVariable) -> pd.DataFrame:
        var_timeseries = self._solution[variable.var_name].to_series()
        return var_timeseries.unstack().pipe(self._drop_single_scenario_level)  # noqa: PD010
