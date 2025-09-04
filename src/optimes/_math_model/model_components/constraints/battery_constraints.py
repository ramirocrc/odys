import linopy
import xarray as xr

from optimes._math_model.model_components.constraints.model_constraint import ModelConstraint
from optimes._math_model.model_components.sets import EnergyModelDimension


def get_battery_max_charge_constraint(
    var_battery_charge: linopy.Variable,
    var_battery_charge_mode: linopy.Variable,
    param_battery_max_power: xr.DataArray,
) -> ModelConstraint:
    # var_battery_discharge <= (1 - var_battery_mode) * param_battery_max_power # noqa: ERA001
    constraint = var_battery_charge <= var_battery_charge_mode * param_battery_max_power  # pyright: ignore reportOperatorIssue
    return ModelConstraint(
        constraint=constraint,
        name="battery_max_charge_constraint",
    )


def get_battery_max_discharge_constraint(
    var_battery_discharge: linopy.Variable,
    var_battery_charge_mode: linopy.Variable,
    param_battery_max_power: xr.DataArray,
) -> ModelConstraint:
    # var_battery_discharge <= (1 - var_battery_mode) * param_battery_max_power # noqa: ERA001
    constraint = (
        var_battery_discharge + var_battery_charge_mode * param_battery_max_power  # pyright: ignore reportOperatorIssue
        <= param_battery_max_power
    )
    return ModelConstraint(
        constraint=constraint,
        name="battery_max_discharge_constraint",
    )


def get_battery_soc_dynamics_constraint(
    var_battery_soc: linopy.Variable,
    var_battery_charge: linopy.Variable,
    var_battery_discharge: linopy.Variable,
    param_battery_efficiency_charging: xr.DataArray,
    param_battery_efficiency_discharging: xr.DataArray,
) -> ModelConstraint:
    time_coords = var_battery_soc.coords[EnergyModelDimension.Time.value]
    constraint_expr = var_battery_soc - (
        var_battery_soc.shift(time=1)
        + param_battery_efficiency_charging * var_battery_charge
        - 1 / param_battery_efficiency_discharging * var_battery_discharge
    )

    constraint = constraint_expr.where(time_coords > time_coords[0]) == 0
    return ModelConstraint(
        constraint=constraint,
        name="battery_soc_dynamics_constraint",
    )


def get_battery_soc_start_constraint(  # noqa: PLR0913
    var_battery_soc: linopy.Variable,
    var_battery_charge: linopy.Variable,
    var_battery_discharge: linopy.Variable,
    param_battery_efficiency_charging: xr.DataArray,
    param_battery_efficiency_discharging: xr.DataArray,
    param_battery_soc_initial: xr.DataArray,
) -> ModelConstraint:
    t0 = var_battery_soc.coords[EnergyModelDimension.Time.value][0]

    soc_t0 = var_battery_soc.sel(time=t0)
    charge_t0 = var_battery_charge.sel(time=t0)
    discharge_t0 = var_battery_discharge.sel(time=t0)

    constraint_expr = (
        soc_t0
        - param_battery_soc_initial
        - param_battery_efficiency_charging * charge_t0
        + 1 / param_battery_efficiency_discharging * discharge_t0
    )

    constraint = constraint_expr == 0
    return ModelConstraint(
        constraint=constraint,
        name="battery_soc_start_constraint",
    )


def get_battery_soc_end_constraint(
    var_battery_soc: linopy.Variable,
    param_battery_soc_end: xr.DataArray,
) -> ModelConstraint:
    time_coords = var_battery_soc.coords[EnergyModelDimension.Time.value]
    constr_expression = var_battery_soc.loc[time_coords.values[-1]] - param_battery_soc_end
    constraint = constr_expression == 0
    return ModelConstraint(
        constraint=constraint,
        name="battery_soc_end_constraint",
    )


def get_battery_soc_bounds_constraint(
    var_battery_soc: linopy.Variable,
    param_battery_capacity: xr.DataArray,
) -> ModelConstraint:
    constraint = var_battery_soc <= param_battery_capacity  # pyright: ignore reportOperatorIssue
    return ModelConstraint(
        constraint=constraint,
        name="battery_soc_bounds_constraint",
    )


def get_battery_net_power_constraint(
    var_battery_net_power: linopy.Variable,
    var_battery_charge: linopy.Variable,
    var_battery_discharge: linopy.Variable,
) -> ModelConstraint:
    constraint = var_battery_net_power == var_battery_charge - var_battery_discharge  # pyright: ignore reportOperatorIssue
    return ModelConstraint(
        constraint=constraint,
        name="battery_net_power_constraint",
    )
