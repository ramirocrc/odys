"""Solution schema and name constants for the results layer.

String values must match linopy coordinate / variable names produced by the
optimization model (see ``ModelDimension`` / ``ModelVariable``). Results must
not import optimization packages — keep this module a leaf.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    import xarray as xr
    from linopy.constants import SolverStatus, TerminationCondition

DIM_SCENARIO = "scenario"
DIM_TIME = "time"
DIM_GENERATOR = "generator"
DIM_STANDALONE_STORAGE = "standalone_storage"
DIM_FLEXIBLE_LOAD = "flexible_load"
DIM_MARKET = "market"
DIM_CHARGER = "charger"
DIM_EV = "ev"

VAR_GENERATOR_POWER = "generator_power"
VAR_GENERATOR_STATUS = "generator_status"
VAR_GENERATOR_STARTUP = "generator_startup"
VAR_GENERATOR_SHUTDOWN = "generator_shutdown"
VAR_STANDALONE_STORAGE_NET_POWER = "standalone_storage_net_power"
VAR_STANDALONE_STORAGE_SOC = "standalone_storage_soc"
VAR_STANDALONE_STORAGE_CHARGE_MODE = "standalone_storage_charge_mode"
VAR_EV_POWER_IN = "ev_power_in"
VAR_EV_NET_POWER = "ev_net_power"
VAR_EV_SOC = "ev_soc"
VAR_EV_CHARGE_MODE = "ev_charge_mode"
VAR_MARKET_SELL = "market_sell_volume"
VAR_MARKET_BUY = "market_buy_volume"
VAR_LOAD_ADJUSTMENT = "load_adjustment"
VAR_CHARGER_EV_ASSIGNMENT = "charger_ev_assignment"


def squeeze_single_scenario(data: xr.Dataset | xr.DataArray) -> xr.Dataset | xr.DataArray:
    """Drop the scenario dimension when it has a single label."""
    if DIM_SCENARIO in data.coords and len(data.coords[DIM_SCENARIO]) == 1:
        return data.squeeze(DIM_SCENARIO, drop=True)
    return data


@dataclass(frozen=True, slots=True)
class SolutionSchema:
    """Boundary DTO between solver and public results views."""

    solver_status: SolverStatus
    termination_condition: TerminationCondition
    solution: xr.Dataset
    objective_value: float | None
    flexible_load_base_profiles: xr.DataArray | None = None

    @classmethod
    def from_solve(
        cls,
        *,
        solver_status: SolverStatus,
        termination_condition: TerminationCondition,
        solution: xr.Dataset,
        objective_value: float | None,
        flexible_load_base_profiles: xr.DataArray | None = None,
    ) -> SolutionSchema:
        """Build a schema with consistent single-scenario squeezing."""
        squeezed_solution = cast("xr.Dataset", squeeze_single_scenario(solution))
        squeezed_base: xr.DataArray | None = None
        if flexible_load_base_profiles is not None:
            squeezed_base = cast("xr.DataArray", squeeze_single_scenario(flexible_load_base_profiles))
        return cls(
            solver_status=solver_status,
            termination_condition=termination_condition,
            solution=squeezed_solution,
            objective_value=objective_value,
            flexible_load_base_profiles=squeezed_base,
        )
