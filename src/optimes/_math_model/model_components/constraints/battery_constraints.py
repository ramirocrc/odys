from typing import ClassVar

import linopy
import xarray as xr

from optimes._math_model.model_components.constraints.base_constraint import SystemConstraint
from optimes._math_model.model_components.constraints.constraint_names import EnergyModelConstraintName


class BatteryChargeModeConstraint(SystemConstraint):
    _name: ClassVar = EnergyModelConstraintName.BATTERY_CHARGE_LIMIT
    var_battery_charge: linopy.Variable
    var_battery_charge_mode: linopy.Variable
    param_battery_max_power: xr.DataArray

    @property
    def constraint(self) -> linopy.Constraint:
        # expression is: var_battery_discharge <= (1 - var_battery_mode) * param_battery_max_power
        return self.var_battery_charge <= self.var_battery_charge_mode * self.param_battery_max_power  # pyright: ignore reportOperatorIssue


class BatteryDischargeModeConstraint(SystemConstraint):
    _name: ClassVar = EnergyModelConstraintName.BATTERY_DISCHARGE_LIMIT
    var_battery_discharge: linopy.Variable
    var_battery_charge_mode: linopy.Variable
    param_battery_max_power: xr.DataArray

    @property
    def constraint(self) -> linopy.Constraint:
        # var_battery_discharge <= (1 - var_battery_mode) * param_battery_max_power # noqa: ERA001
        return (
            self.var_battery_discharge + self.var_battery_charge_mode * self.param_battery_max_power  # pyright: ignore reportOperatorIssue
            <= self.param_battery_max_power
        )


class BatterySocDynamicsConstraint(SystemConstraint):
    """Battery state of charge dynamics constraint.

    This constraint models the evolution of battery state of charge over time,
    accounting for charging and discharging with efficiency losses.
    Handles both initial conditions and time evolution in a unified manner.
    """

    _name: ClassVar = EnergyModelConstraintName.BATTERY_SOC_DYNAMICS
    var_battery_soc: linopy.Variable
    var_battery_charge: linopy.Variable
    var_battery_discharge: linopy.Variable
    param_battery_efficiency_charging: xr.DataArray
    param_battery_efficiency_discharging: xr.DataArray

    @property
    def constraint(self) -> linopy.Constraint:
        # Use shift with fill_value to handle the first timestep
        time_coords = self.var_battery_soc.coords["time"]
        constraint_expr = self.var_battery_soc - (
            self.var_battery_soc.shift(time=1)
            + self.param_battery_efficiency_charging * self.var_battery_charge
            - 1 / self.param_battery_efficiency_discharging * self.var_battery_discharge
        )

        return constraint_expr.where(time_coords > time_coords[0]) == 0


class BatterySocStartConstraint(SystemConstraint):
    """Battery state of charge dynamics constraint.

    This constraint models the evolution of battery state of charge over time,
    accounting for charging and discharging with efficiency losses.
    Handles both initial conditions and time evolution in a unified manner.
    """

    _name: ClassVar = EnergyModelConstraintName.BATTERY_SOC_START
    var_battery_soc: linopy.Variable
    var_battery_charge: linopy.Variable
    var_battery_discharge: linopy.Variable
    param_battery_efficiency_charging: xr.DataArray
    param_battery_efficiency_discharging: xr.DataArray
    param_battery_soc_initial: xr.DataArray

    @property
    def constraint(self) -> linopy.Constraint:
        t0 = self.var_battery_soc.coords["time"][0]

        # Select all variables for t=0 (efficiency parameters are time-independent)
        soc_t0 = self.var_battery_soc.sel(time=t0)
        charge_t0 = self.var_battery_charge.sel(time=t0)
        discharge_t0 = self.var_battery_discharge.sel(time=t0)

        constraint_expr = (
            soc_t0
            - self.param_battery_soc_initial
            - self.param_battery_efficiency_charging * charge_t0
            + 1 / self.param_battery_efficiency_discharging * discharge_t0
        )

        return constraint_expr == 0


class BatterySocEndtConstraint(SystemConstraint):
    """Battery state of charge dynamics constraint.

    This constraint models the evolution of battery state of charge over time,
    accounting for charging and discharging with efficiency losses.
    """

    _name: ClassVar = EnergyModelConstraintName.BATTERY_SOC_END
    var_battery_soc: linopy.Variable
    param_battery_soc_end: xr.DataArray

    @property
    def constraint(self) -> linopy.Constraint:
        time_coords = self.var_battery_soc.coords["time"]

        constr_expression = self.var_battery_soc.loc[time_coords.values[-1]] - self.param_battery_soc_end
        return constr_expression == 0


class BatterySocEndConstraint(SystemConstraint):
    """Battery terminal state of charge constraint.

    This constraint ensures that the battery reaches the specified
    terminal state of charge at the end of the optimization period.
    """

    _name: ClassVar = EnergyModelConstraintName.BATTERY_SOC_BOUNDS
    var_battery_soc: linopy.Variable
    param_battery_capacity: xr.DataArray

    @property
    def constraint(self) -> linopy.Constraint:
        return self.var_battery_soc <= self.param_battery_capacity
