"""Frozen snapshot of solved model data for result extraction."""

import xarray as xr
from linopy.constants import SolverStatus, TerminationCondition

from odys.domain.exceptions import OdysNoResultsError, OdysSolverError
from odys.optimization.formulations.charging import ChargingFormulation
from odys.optimization.formulations.electric_vehicle import ElectricVehicleFormulation
from odys.optimization.formulations.energy_market import EnergyMarketFormulation
from odys.optimization.formulations.flexible_load import FlexibleLoadFormulation
from odys.optimization.formulations.generator import GeneratorFormulation
from odys.optimization.formulations.stationary_storage import StationaryStorageFormulation
from odys.optimization.problem import OptimizationProblem
from odys.parameters.dimensions import ModelDimension
from odys.results.dispatch import (
    ChargerDispatch,
    ElectricVehicleDispatch,
    FlexibleLoadDispatch,
    GeneratorDispatch,
    MarketDispatch,
    StationaryStorageDispatch,
)


class OptimalDispatchResults:
    """Frozen snapshot of data extracted from a solved EnergyMILPModel.

    Captures only what OptimizationResults needs, allowing the full
    linopy model to be garbage-collected after solving.
    """

    __slots__ = (
        "_objective_value",
        "_problem",
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
        problem: OptimizationProblem,
    ) -> None:
        """Initialize OptimalDispatchResults."""
        self._solver_status = solver_status
        self._termination_condition = termination_condition
        if ModelDimension.Scenarios in solution.coords and len(solution.coords[ModelDimension.Scenarios]) == 1:
            solution = solution.squeeze(ModelDimension.Scenarios, drop=True)
        self._solution = solution
        self._objective_value = objective_value
        self._variable_names = set(solution.variables.keys())
        self._problem = problem

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
        if self._problem.formulation_of(GeneratorFormulation) is None:
            msg = "This model does not contain generator results"
            raise OdysNoResultsError(msg)

        return GeneratorDispatch(
            power=self._solution[GeneratorFormulation.power_name],
            status=self._solution[GeneratorFormulation.status_name],
            startup=self._solution[GeneratorFormulation.startup_name],
            shutdown=self._solution[GeneratorFormulation.shutdown_name],
        )

    @property
    def stationary_storages(self) -> StationaryStorageDispatch:
        """Get stationary storage dispatch results."""
        self._validate_terminated_successfully()
        if self._problem.formulation_of(StationaryStorageFormulation) is None:
            msg = "This model does not contain stationary storage results"
            raise OdysNoResultsError(msg)

        return StationaryStorageDispatch(
            net_power=self._solution[StationaryStorageFormulation.net_power_name],
            soc=self._solution[StationaryStorageFormulation.soc_name],
            charge_mode=self._solution[StationaryStorageFormulation.charge_mode_name],
        )

    @property
    def electric_vehicles(self) -> ElectricVehicleDispatch:
        """Get electric vehicle dispatch results."""
        self._validate_terminated_successfully()
        if self._problem.formulation_of(ElectricVehicleFormulation) is None:
            msg = "This model does not contain electric vehicle results"
            raise OdysNoResultsError(msg)

        return ElectricVehicleDispatch(
            net_power=self._solution[ElectricVehicleFormulation.net_power_name],
            soc=self._solution[ElectricVehicleFormulation.soc_name],
            charge_mode=self._solution[ElectricVehicleFormulation.charge_mode_name],
        )

    @property
    def chargers(self) -> ChargerDispatch:
        """Get charger dispatch results."""
        self._validate_terminated_successfully()
        if self._problem.formulation_of(ChargingFormulation) is None:
            msg = "This model does not contain charger results"
            raise OdysNoResultsError(msg)

        return ChargerDispatch(
            assignment=self._solution[ChargingFormulation.assignment_name],
            power_in=self._solution[ElectricVehicleFormulation.power_in_name],
        )

    @property
    def markets(self) -> MarketDispatch:
        """Get market dispatch results."""
        self._validate_terminated_successfully()
        if self._problem.formulation_of(EnergyMarketFormulation) is None:
            msg = "This model does not contain market results"
            raise OdysNoResultsError(msg)

        return MarketDispatch(
            sell_volume=self._solution[EnergyMarketFormulation.sell_volume_name],
            buy_volume=self._solution[EnergyMarketFormulation.buy_volume_name],
        )

    @property
    def flexible_loads(self) -> FlexibleLoadDispatch:
        """Get flexible load dispatch results."""
        self._validate_terminated_successfully()
        flexible_loads = self._problem.formulation_of(FlexibleLoadFormulation)
        if flexible_loads is None:
            msg = "This model does not contain flexible load results"
            raise OdysNoResultsError(msg)
        base_profiles = flexible_loads.base_profiles

        if ModelDimension.Scenarios in base_profiles.dims and len(base_profiles.coords[ModelDimension.Scenarios]) == 1:
            base_profiles = base_profiles.squeeze(ModelDimension.Scenarios, drop=True)

        return FlexibleLoadDispatch(
            load_adjustment=self._solution[FlexibleLoadFormulation.variable_name],
            base_profiles=base_profiles,
        )

    @property
    def objective_value(self) -> float | None:
        """Objective value from optimization."""
        self._validate_terminated_successfully()
        return self._objective_value
