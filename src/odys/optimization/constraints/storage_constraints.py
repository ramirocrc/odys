"""Shared battery constraint builders for storage-like assets.

Provides reusable constraint-building functions for assets that share
battery physics (StandaloneStorage, ElectricVehicle). Each function
accepts variable and parameter references and returns a ModelConstraint.
"""

import xarray as xr
from linopy import Variable

from odys.optimization.constraints.model_constraint import ModelConstraint
from odys.optimization.model.sets import ModelDimension


def build_max_charge_constraint(
    power_in: Variable,
    charge_mode: Variable,
    max_charge_power: xr.DataArray,
    name: str,
) -> ModelConstraint:
    """Maximum charging power limited by max_charge_power when in charging mode."""
    return ModelConstraint(
        constraint=power_in <= charge_mode * max_charge_power,
        name=name,
    )


def build_max_discharge_constraint(
    power_out: Variable,
    charge_mode: Variable,
    max_discharge_power: xr.DataArray,
    name: str,
) -> ModelConstraint:
    """Maximum discharging power limited by max_discharge_power when in discharging mode."""
    return ModelConstraint(
        constraint=power_out + charge_mode * max_discharge_power <= max_discharge_power,
        name=name,
    )


def build_soc_dynamics_constraint(  # noqa: PLR0913
    soc: Variable,
    power_in: Variable,
    power_out: Variable,
    self_discharge_rate: xr.DataArray,
    efficiency_charging: xr.DataArray,
    efficiency_discharging: xr.DataArray,
    capacity: xr.DataArray,
    timestep_hours: float,
    name: str,
) -> ModelConstraint:
    """SOC time-stepping dynamics with self-discharge and charge/discharge efficiency."""
    dt = timestep_hours
    time_coords = soc.coords[ModelDimension.Time.value]
    constraint_expr = soc - (
        soc.shift(time=1) * (1 - self_discharge_rate * dt)
        + efficiency_charging * power_in * dt / capacity
        - 1 / efficiency_discharging * power_out * dt / capacity
    )
    return ModelConstraint(
        constraint=constraint_expr.where(time_coords > time_coords[0]) == 0,
        name=name,
    )


def build_soc_start_constraint(  # noqa: PLR0913
    soc: Variable,
    power_in: Variable,
    power_out: Variable,
    soc_start: xr.DataArray,
    efficiency_charging: xr.DataArray,
    efficiency_discharging: xr.DataArray,
    capacity: xr.DataArray,
    timestep_hours: float,
    name: str,
) -> ModelConstraint:
    """Initial SOC constraint at t=0."""
    dt = timestep_hours
    t0 = soc.coords[ModelDimension.Time.value][0]
    soc_t0 = soc.sel(time=t0)
    charge_t0 = power_in.sel(time=t0)
    discharge_t0 = power_out.sel(time=t0)
    constraint_expr = (
        soc_t0
        - soc_start
        - efficiency_charging * charge_t0 * dt / capacity
        + 1 / efficiency_discharging * discharge_t0 * dt / capacity
    )
    return ModelConstraint(
        constraint=constraint_expr == 0,
        name=name,
    )


def build_soc_end_constraint(
    soc: Variable,
    soc_end: xr.DataArray,
    asset_dimension: str,
    name: str,
) -> ModelConstraint | list[ModelConstraint]:
    """Final SOC target constraint (only for assets with soc_end set)."""
    has_soc_end = soc_end.notnull()
    if not has_soc_end.any():
        return []

    time_coords = soc.coords[ModelDimension.Time.value]
    last_time = time_coords.values[-1]
    lhs = soc.sel(time=last_time).sel({asset_dimension: has_soc_end})
    rhs = soc_end.sel({asset_dimension: has_soc_end})

    return ModelConstraint(
        constraint=lhs - rhs == 0,
        name=name,
    )


def build_soc_min_constraint(
    soc: Variable,
    soc_min: xr.DataArray,
    name: str,
) -> ModelConstraint:
    """Minimum SOC constraint."""
    return ModelConstraint(
        constraint=soc >= soc_min,
        name=name,
    )


def build_soc_max_constraint(
    soc: Variable,
    soc_max: xr.DataArray,
    name: str,
) -> ModelConstraint:
    """Maximum SOC constraint."""
    return ModelConstraint(
        constraint=soc <= soc_max,
        name=name,
    )


def build_capacity_constraint(
    soc: Variable,
    name: str,
) -> ModelConstraint:
    """SOC capacity upper bound (SOC <= 1)."""
    return ModelConstraint(
        constraint=soc <= 1,  # pyrefly: ignore
        name=name,
    )


def build_net_power_constraint(
    power_net: Variable,
    power_in: Variable,
    power_out: Variable,
    name: str,
) -> ModelConstraint:
    """Net power definition: power_net == power_in - power_out."""
    return ModelConstraint(
        constraint=power_net == power_in - power_out,
        name=name,
    )
