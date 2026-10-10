"""Dispatch results of one solve."""

from collections.abc import Callable, Sequence
from typing import TypeVar

import xarray as xr

from odys.domain.exceptions import OdysNoResultsError, OdysSolverError
from odys.parameters.dimensions import ModelDimension
from odys.results.dispatch import (
    ChargerDispatch,
    Dispatch,
    ElectricVehicleDispatch,
    FlexibleLoadDispatch,
    GeneratorDispatch,
    MarketDispatch,
    StationaryStorageDispatch,
)
from odys.solvers.outcome import SolveOutcome, SolveStatus

DispatchT = TypeVar("DispatchT", bound=Dispatch)


class OptimalDispatchResults:
    """Dispatch results of one solve: the solver status, the objective value and one dispatch per entity type."""

    __slots__ = (
        "_dispatches",
        "_has_solution",
        "_objective_value",
        "_solution",
        "_solver_status",
        "_termination_condition",
    )

    def __init__(
        self,
        outcome: SolveOutcome,
        build_dispatches: Callable[[xr.Dataset], Sequence[Dispatch]],
    ) -> None:
        """Initialize from the solve outcome and the function that reads the dispatches from its solution.

        Args:
            outcome: What the solver returned.
            build_dispatches: Returns one dispatch per entity type from the solution
                (`OptimizationProblem.dispatches`); called only when the outcome has a solution.
                It gets the solution with its scenario dimension, and each dispatch is squeezed
                afterwards: derived series such as the flexible-load actual load add scenario-indexed
                parameters, which would broadcast the dimension back if the solution were squeezed first.
        """
        self._solver_status = outcome.status
        self._termination_condition = outcome.termination_condition
        self._has_solution = outcome.has_solution
        self._objective_value = outcome.objective_value
        self._solution = _without_single_scenario(outcome.solution)
        dispatches = build_dispatches(outcome.solution) if outcome.has_solution else ()
        self._dispatches: dict[type[Dispatch], Dispatch] = {
            type(dispatch): type(dispatch)(_without_single_scenario(dispatch.to_dataset()), dispatch.dimension)
            for dispatch in dispatches
        }

    @property
    def solver_status(self) -> SolveStatus:
        """Get the solver status."""
        return self._solver_status

    @property
    def termination_condition(self) -> str:
        """Get the termination condition."""
        return self._termination_condition

    def to_dataset(self) -> xr.Dataset:
        """Get the raw solution dataset."""
        self._validate_terminated_successfully()
        return self._solution

    def _validate_terminated_successfully(self) -> None:
        if not self._has_solution:
            msg = f"No solution available. Optimization Termination Condition: {self._termination_condition}."
            raise OdysSolverError(msg)

    def _dispatch_of(self, kind: type[DispatchT]) -> DispatchT:
        self._validate_terminated_successfully()
        dispatch = self._dispatches.get(kind)
        if not isinstance(dispatch, kind):
            msg = f"This model does not contain {kind.label} results"
            raise OdysNoResultsError(msg)
        return dispatch

    @property
    def generators(self) -> GeneratorDispatch:
        """Get generator dispatch results."""
        return self._dispatch_of(GeneratorDispatch)

    @property
    def stationary_storages(self) -> StationaryStorageDispatch:
        """Get stationary storage dispatch results."""
        return self._dispatch_of(StationaryStorageDispatch)

    @property
    def electric_vehicles(self) -> ElectricVehicleDispatch:
        """Get electric vehicle dispatch results."""
        return self._dispatch_of(ElectricVehicleDispatch)

    @property
    def chargers(self) -> ChargerDispatch:
        """Get charger dispatch results."""
        return self._dispatch_of(ChargerDispatch)

    @property
    def markets(self) -> MarketDispatch:
        """Get market dispatch results."""
        return self._dispatch_of(MarketDispatch)

    @property
    def flexible_loads(self) -> FlexibleLoadDispatch:
        """Get flexible load dispatch results."""
        return self._dispatch_of(FlexibleLoadDispatch)

    @property
    def objective_value(self) -> float | None:
        """Objective value from optimization."""
        self._validate_terminated_successfully()
        return self._objective_value


def _without_single_scenario(data: xr.Dataset) -> xr.Dataset:
    """Drop the scenario dimension of a single-scenario run, so results read like a deterministic run."""
    scenarios = ModelDimension.Scenarios
    if scenarios in data.dims and data.sizes[scenarios] == 1:
        squeezed: xr.Dataset = data.squeeze(scenarios, drop=True)
        return squeezed
    return data
