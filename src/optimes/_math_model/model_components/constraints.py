"""Constraint definitions for energy system optimization models.

This module defines constraint names and types used in energy system
optimization models.
"""

from abc import ABC, abstractmethod
from enum import Enum, unique
from typing import ClassVar

import linopy
import xarray as xr
from pydantic import BaseModel


@unique
class EnergyModelConstraintName(Enum):
    """Enumeration of constraint names used in the energy model."""

    POWER_BALANCE = "const_power_balance"
    GENERATOR_LIMIT = "const_generator_limit"
    BATTERY_CHARGE_LIMIT = "const_battery_charge_limit"
    BATTERY_DISCHARGE_LIMIT = "const_battery_discharge_limit"
    BATTERY_SOC_DYNAMICS = "const_battery_soc_dynamics"
    BATTERY_SOC_BOUNDS = "const_battery_soc_bounds"
    BATTERY_SOC_END = "const_battery_soc_end"


class SystemConstraint(ABC, BaseModel, arbitrary_types_allowed=True, extra="forbid"):
    """Abstract base class for system constraints.

    This class defines the interface for all constraints in the energy system
    model, providing a common structure for constraint implementation.
    """

    _name: ClassVar[EnergyModelConstraintName]

    @property
    def name(self) -> EnergyModelConstraintName:
        """Get the constraint name.

        Returns:
            The constraint name enum value.

        """
        return self._name

    @property
    @abstractmethod
    def constraint(self) -> linopy.Constraint:
        """Get the Pyomo constraint.

        This abstract method must be implemented by subclasses to
        define the specific constraint logic.

        Returns:
            The Pyomo constraint object.

        """


class PowerBalanceConstraint(SystemConstraint):
    """Linopy power balance constraint ensuring supply equals demand.

    This constraint ensures that at each time period, the total power
    generation plus battery discharge equals the demand plus battery charging.
    """

    _name: ClassVar = EnergyModelConstraintName.POWER_BALANCE
    var_generator_power: linopy.Variable
    var_battery_discharge: linopy.Variable
    var_battery_charge: linopy.Variable
    demand_profile: xr.DataArray

    @property
    def constraint(self) -> linopy.Constraint:
        """Get the power balance constraint expression.

        Returns:
            Linopy expression that equals zero when satisfied.
        """
        generation_total = self.var_generator_power.sum("generators")
        discharge_total = self.var_battery_discharge.sum("batteries")
        charge_total = self.var_battery_charge.sum("batteries")

        return generation_total + discharge_total - charge_total - self.demand_profile == 0


class GenerationLimitConstraint(SystemConstraint):
    """Generator power limit constraint.

    This constraint ensures that each generator's power output does not
    exceed its nominal power capacity.
    """

    _name: ClassVar = EnergyModelConstraintName.GENERATOR_LIMIT
    var_generator_power: linopy.Variable
    param_generator_nominal_power: xr.DataArray

    @property
    def constraint(self) -> linopy.Constraint:
        return self.var_generator_power <= self.param_generator_nominal_power


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
    param_battery_soc_initial: xr.DataArray

    @property
    def constraint(self) -> linopy.Constraint:
        # Use shift with fill_value to handle the first timestep
        previous_soc = self.var_battery_soc.shift(time=1, fill_value=self.param_battery_soc_initial)

        constraint_expr = self.var_battery_soc - (
            previous_soc
            + self.param_battery_efficiency_charging * self.var_battery_charge
            - 1 / self.param_battery_efficiency_discharging * self.var_battery_discharge
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

        constr_expression = self.var_battery_soc.loc[time_coords[-1]] - self.param_battery_soc_end
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
