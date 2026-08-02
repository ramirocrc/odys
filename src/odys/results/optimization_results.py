"""Frozen snapshot of solved model data for result extraction."""

from __future__ import annotations

from typing import TYPE_CHECKING

from linopy.constants import SolverStatus

from odys.domain.exceptions import OdysNoResultsError, OdysSolverError
from odys.results.dispatch import (
    ChargerDispatch,
    ElectricVehicleDispatch,
    FlexibleLoadDispatch,
    GeneratorDispatch,
    MarketDispatch,
    StandaloneStorageDispatch,
)
from odys.results.schema import (
    DIM_CHARGER,
    DIM_EV,
    DIM_FLEXIBLE_LOAD,
    DIM_GENERATOR,
    DIM_MARKET,
    DIM_STANDALONE_STORAGE,
    VAR_CHARGER_EV_ASSIGNMENT,
    VAR_EV_CHARGE_MODE,
    VAR_EV_NET_POWER,
    VAR_EV_POWER_IN,
    VAR_EV_SOC,
    VAR_GENERATOR_POWER,
    VAR_GENERATOR_SHUTDOWN,
    VAR_GENERATOR_STARTUP,
    VAR_GENERATOR_STATUS,
    VAR_LOAD_ADJUSTMENT,
    VAR_MARKET_BUY,
    VAR_MARKET_SELL,
    VAR_STANDALONE_STORAGE_CHARGE_MODE,
    VAR_STANDALONE_STORAGE_NET_POWER,
    VAR_STANDALONE_STORAGE_SOC,
    SolutionSchema,
)

if TYPE_CHECKING:
    import xarray as xr


class OptimalDispatchResults:
    """Frozen snapshot of data extracted from a solved optimization model.

    Holds a :class:`SolutionSchema` only — not the full linopy model or
    ``EnergySystemParameters`` — so algebraic internals can be GC'd after solve.
    """

    __slots__ = (
        "_has_chargers",
        "_has_electric_vehicles",
        "_has_flexible_loads",
        "_has_generators",
        "_has_markets",
        "_has_standalone_storages",
        "_schema",
    )

    def __init__(self, schema: SolutionSchema) -> None:
        """Initialize from a solver-built solution schema."""
        self._schema = schema
        solution = schema.solution
        self._has_generators = DIM_GENERATOR in solution.dims
        self._has_standalone_storages = DIM_STANDALONE_STORAGE in solution.dims
        self._has_electric_vehicles = DIM_EV in solution.dims
        self._has_chargers = DIM_CHARGER in solution.dims
        self._has_markets = DIM_MARKET in solution.dims
        self._has_flexible_loads = DIM_FLEXIBLE_LOAD in solution.dims

    @property
    def solver_status(self) -> str:
        """Get the solver status."""
        return self._schema.solver_status.value

    @property
    def termination_condition(self) -> str:
        """Get the termination condition."""
        return self._schema.termination_condition.value

    def to_dataset(self) -> xr.Dataset:
        """Get the raw solution dataset."""
        self._validate_terminated_successfully()
        return self._schema.solution

    def _validate_terminated_successfully(self) -> None:
        if self._schema.solver_status != SolverStatus.ok:
            msg = f"No solution available. Optimization Termination Condition: {self._schema.termination_condition}."
            raise OdysSolverError(msg)

    @property
    def generators(self) -> GeneratorDispatch:
        """Get generator dispatch results."""
        self._validate_terminated_successfully()
        if not self._has_generators:
            msg = "This model does not contain generator results"
            raise OdysNoResultsError(msg)
        solution = self._schema.solution
        return GeneratorDispatch(
            power=solution[VAR_GENERATOR_POWER],
            status=solution[VAR_GENERATOR_STATUS],
            startup=solution[VAR_GENERATOR_STARTUP],
            shutdown=solution[VAR_GENERATOR_SHUTDOWN],
        )

    @property
    def standalone_storages(self) -> StandaloneStorageDispatch:
        """Get standalone storage dispatch results."""
        self._validate_terminated_successfully()
        if not self._has_standalone_storages:
            msg = "This model does not contain standalone storage results"
            raise OdysNoResultsError(msg)
        solution = self._schema.solution
        return StandaloneStorageDispatch(
            net_power=solution[VAR_STANDALONE_STORAGE_NET_POWER],
            soc=solution[VAR_STANDALONE_STORAGE_SOC],
            charge_mode=solution[VAR_STANDALONE_STORAGE_CHARGE_MODE],
        )

    @property
    def electric_vehicles(self) -> ElectricVehicleDispatch:
        """Get electric vehicle dispatch results."""
        self._validate_terminated_successfully()
        if not self._has_electric_vehicles:
            msg = "This model does not contain electric vehicle results"
            raise OdysNoResultsError(msg)
        solution = self._schema.solution
        return ElectricVehicleDispatch(
            net_power=solution[VAR_EV_NET_POWER],
            soc=solution[VAR_EV_SOC],
            charge_mode=solution[VAR_EV_CHARGE_MODE],
        )

    @property
    def chargers(self) -> ChargerDispatch:
        """Get charger dispatch results."""
        self._validate_terminated_successfully()
        if not self._has_chargers:
            msg = "This model does not contain charger results"
            raise OdysNoResultsError(msg)
        solution = self._schema.solution
        return ChargerDispatch(
            assignment=solution[VAR_CHARGER_EV_ASSIGNMENT],
            power_in=solution[VAR_EV_POWER_IN],
        )

    @property
    def markets(self) -> MarketDispatch:
        """Get market dispatch results."""
        self._validate_terminated_successfully()
        if not self._has_markets:
            msg = "This model does not contain market results"
            raise OdysNoResultsError(msg)
        solution = self._schema.solution
        return MarketDispatch(
            sell_volume=solution[VAR_MARKET_SELL],
            buy_volume=solution[VAR_MARKET_BUY],
        )

    @property
    def flexible_loads(self) -> FlexibleLoadDispatch:
        """Get flexible load dispatch results."""
        self._validate_terminated_successfully()
        if not self._has_flexible_loads:
            msg = "This model does not contain flexible load results"
            raise OdysNoResultsError(msg)
        base_profiles = self._schema.flexible_load_base_profiles
        if base_profiles is None:
            msg = "Flexible loads exist but base profiles are missing"
            raise OdysNoResultsError(msg)
        return FlexibleLoadDispatch(
            load_adjustment=self._schema.solution[VAR_LOAD_ADJUSTMENT],
            base_profiles=base_profiles,
        )

    @property
    def objective_value(self) -> float | None:
        """Objective value from optimization."""
        self._validate_terminated_successfully()
        return self._schema.objective_value
