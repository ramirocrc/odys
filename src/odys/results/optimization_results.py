"""Frozen snapshot of solved model data for result extraction."""

import xarray as xr
from linopy.constants import SolverStatus, TerminationCondition

from odys.domain.exceptions import OdysNoResultsError, OdysSolverError
from odys.optimization.model.sets import ModelDimension
from odys.optimization.model.variables import ModelVariable
from odys.results.dispatch import (
    GeneratorDispatch,
    MarketDispatch,
    StorageDispatch,
)


class OptimalDisptachResults:
    """Frozen snapshot of data extracted from a solved EnergyMILPModel.

    Captures only what OptimizationResults needs, allowing the full
    linopy model to be garbage-collected after solving.
    """

    __slots__ = (
        "_has_generators",
        "_has_markets",
        "_has_storages",
        "_objective_value",
        "_solution",
        "_solver_status",
        "_termination_condition",
        "_variable_names",
    )

    def __init__(
        self,
        solver_status: SolverStatus,
        termination_condition: TerminationCondition,
        solution: xr.Dataset,
        objective_value: float | None,
    ) -> None:
        """Initialize OptimalDisptachResults."""
        self._solver_status = solver_status
        self._termination_condition = termination_condition
        if ModelDimension.Scenarios in solution.coords and len(solution.coords[ModelDimension.Scenarios]) == 1:
            solution = solution.squeeze(ModelDimension.Scenarios, drop=True)
        self._solution = solution
        self._objective_value = objective_value
        self._variable_names = set(solution.variables.keys())
        self._has_generators = ModelDimension.Generators in solution.dims
        self._has_storages = ModelDimension.Storages in solution.dims
        self._has_markets = ModelDimension.Markets in solution.dims

    @property
    def solver_status(self) -> str:
        """Get the solver status."""
        return self._solver_status.value

    @property
    def termination_condition(self) -> str:
        """Get the termination condition."""
        return self._termination_condition.value

    def to_dataset(self) -> xr.Dataset:
        """Get the raw solution dataset."""
        self._validate_terminated_successfully()
        return self._solution

    def _validate_terminated_successfully(self) -> None:
        if self._solver_status != SolverStatus.ok:
            msg = f"No solution available. Optimization Termination Condition: {self._termination_condition}."
            raise OdysSolverError(msg)

    @property
    def generators(self) -> GeneratorDispatch:
        """Get generator dispatch results."""
        self._validate_terminated_successfully()
        if not self._has_generators:
            msg = "This model does not contain generator results"
            raise OdysNoResultsError(msg)

        return GeneratorDispatch(
            power=self._solution[ModelVariable.GENERATOR_POWER.var_name],
            status=self._solution[ModelVariable.GENERATOR_STATUS.var_name],
            startup=self._solution[ModelVariable.GENERATOR_STARTUP.var_name],
            shutdown=self._solution[ModelVariable.GENERATOR_SHUTDOWN.var_name],
        )

    @property
    def storages(self) -> StorageDispatch:
        """Get storage dispatch results."""
        self._validate_terminated_successfully()
        if not self._has_storages:
            msg = "This model does not contain storage results"
            raise OdysNoResultsError(msg)

        return StorageDispatch(
            net_power=self._solution[ModelVariable.STORAGE_POWER_NET.var_name],
            soc=self._solution[ModelVariable.STORAGE_SOC.var_name],
            charge_mode=self._solution[ModelVariable.STORAGE_CHARGE_MODE.var_name],
        )

    @property
    def markets(self) -> MarketDispatch:
        """Get market dispatch results."""
        self._validate_terminated_successfully()
        if not self._has_markets:
            msg = "This model does not contain market results"
            raise OdysNoResultsError(msg)

        return MarketDispatch(
            sell_volume=self._solution[ModelVariable.MARKET_SELL.var_name],
            buy_volume=self._solution[ModelVariable.MARKET_BUY.var_name],
        )

    @property
    def objective_value(self) -> float | None:
        """Objective value from optimization."""
        self._validate_terminated_successfully()
        return self._objective_value
