"""Constraint definitions for energy system optimization models.

This module defines constraint names and types used in energy system
optimization models.
"""

from abc import ABC, abstractmethod
from enum import Enum, unique
from typing import ClassVar

import pyomo.environ as pyo
from pydantic import BaseModel

from optimes._math_model.model_components.sets import EnergyModelSetName


@unique
class EnergyModelConstraintName(Enum):
    """Enumeration of constraint names used in the energy model."""

    POWER_BALANCE = "const_power_balance"
    GENERATOR_LIMIT = "const_generator_limit"
    BATTERY_CHARGE_LIMIT = "const_battery_charge_limit"
    BATTERY_DISCHARGE_LIMIT = "const_battery_discharge_limit"
    BATTERY_SOC_DYNAMICS = "const_battery_soc_dynamics"
    BATTERY_SOC_BOUNDS = "const_battery_soc_bounds"
    BATTERY_SOC_TERMINAL = "const_battery_soc_terminal"


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
    def component(self) -> pyo.Constraint:
        """Get the Pyomo constraint component.

        Returns:
            The Pyomo constraint object.

        """
        return self.constraint

    @property
    @abstractmethod
    def constraint(self) -> pyo.Constraint:
        """Get the Pyomo constraint.

        This abstract method must be implemented by subclasses to
        define the specific constraint logic.

        Returns:
            The Pyomo constraint object.

        """


class PowerBalanceConstraint(SystemConstraint):
    """Power balance constraint ensuring supply equals demand.

    This constraint ensures that at each time period, the total power
    generation plus battery discharge equals the demand plus battery charging.
    """

    _name: ClassVar = EnergyModelConstraintName.POWER_BALANCE
    var_generator_power: pyo.Var
    var_battery_discharge: pyo.Var
    var_battery_charge: pyo.Var
    param_demand: pyo.Param

    @property
    def constraint(self) -> pyo.Constraint:
        """Get the power balance constraint.

        Returns:
            Pyomo constraint ensuring power balance at each time period.

        """

        def rule(m: pyo.ConcreteModel, t: int):  # noqa: ARG001, ANN202
            generation_total = sum(self.var_generator_power[t, i] for i in set_generator)  # pyright: ignore [reportCallIssue, reportArgumentType]
            discharge_total = sum(self.var_battery_discharge[t, j] for j in set_batteries)  # pyright: ignore [reportCallIssue, reportArgumentType]
            charge_total = sum(self.var_battery_charge[t, j] for j in set_batteries)  # pyright: ignore [reportCallIssue, reportArgumentType]
            return generation_total + discharge_total == self.param_demand[t] + charge_total

        set_time, set_generator = self.var_generator_power.index_set().subsets()
        _, set_batteries = self.var_battery_discharge.index_set().subsets()
        return pyo.Constraint(
            set_time,
            rule=rule,
        )


class GenerationLimitConstraint(SystemConstraint):
    """Generator power limit constraint.

    This constraint ensures that each generator's power output does not
    exceed its nominal power capacity.
    """

    _name: ClassVar = EnergyModelConstraintName.GENERATOR_LIMIT
    var_generator_power: pyo.Var
    param_generator_nominal_power: pyo.Param

    @property
    def constraint(self) -> pyo.Constraint:
        """Get the generation limit constraint.

        Returns: Pyomo constraint limiting generator power to nominal capacity.

        """

        def rule(m: pyo.ConcreteModel, t: int, i: int):  # noqa: ARG001, ANN202
            return self.var_generator_power[t, i] <= self.param_generator_nominal_power[i]  # pyright: ignore reportOperatorIssue

        set_time, set_generator = self.var_generator_power.index_set().subsets()
        return pyo.Constraint(
            set_time,
            set_generator,
            rule=rule,
        )


class BatteryChargeModeConstraint(SystemConstraint):
    """Battery charging power limit constraint.

    This constraint ensures that battery charging power does not exceed
    the maximum power when the battery is in charging mode.
    """

    _name: ClassVar = EnergyModelConstraintName.BATTERY_CHARGE_LIMIT
    var_battery_charge: pyo.Var
    var_battery_charge_mode: pyo.Var
    param_battery_max_power: pyo.Param

    @property
    def constraint(self) -> pyo.Constraint:
        """Get the battery charge mode constraint.

        Returns:
            Pyomo constraint limiting battery charging power based on charge mode.

        """

        def rule(m: pyo.ConcreteModel, t: int, j: int):  # noqa: ARG001, ANN202
            return self.var_battery_charge[t, j] <= self.param_battery_max_power[j] * self.var_battery_charge_mode[t, j]  # pyright: ignore reportOperatorIssue

        set_time, set_batteries = self.var_battery_charge.index_set().subsets()
        return pyo.Constraint(
            set_time,
            set_batteries,
            rule=rule,
        )


class BatteryDischargeModeConstraint(SystemConstraint):
    """Battery discharging power limit constraint.

    This constraint ensures that battery discharging power does not exceed
    the maximum power when the battery is in discharging mode.
    """

    _name: ClassVar = EnergyModelConstraintName.BATTERY_DISCHARGE_LIMIT
    var_battery_discharge: pyo.Var
    var_battery_charge_mode: pyo.Var
    param_battery_max_power: pyo.Param

    @property
    def constraint(self) -> pyo.Constraint:
        """Get the battery discharge mode constraint.

        Returns:
            Pyomo constraint limiting battery discharging power based on charge mode.

        """

        def rule(m: pyo.ConcreteModel, t: int, j: int):  # noqa: ARG001, ANN202
            return self.var_battery_discharge[t, j] <= self.param_battery_max_power[j] * (
                1 - self.var_battery_charge_mode[t, j]  # pyright: ignore reportOperatorIssue
            )

        set_time, set_batteries = self.var_battery_discharge.index_set().subsets()
        return pyo.Constraint(
            set_time,
            set_batteries,
            rule=rule,
        )


class BatterySocDynamicsConstraint(SystemConstraint):
    """Battery state of charge dynamics constraint.

    This constraint models the evolution of battery state of charge over time,
    accounting for charging and discharging with efficiency losses.
    """

    _name: ClassVar = EnergyModelConstraintName.BATTERY_SOC_DYNAMICS
    var_battery_soc: pyo.Var
    var_battery_charge: pyo.Var
    var_battery_discharge: pyo.Var
    param_battery_efficiency_charging: pyo.Param
    param_battery_efficiency_discharging: pyo.Param
    param_battery_soc_initial: pyo.Param

    @property
    def constraint(self) -> pyo.Constraint:
        """Get the battery SOC dynamics constraint.

        Returns:
            Pyomo constraint modeling SOC evolution over time.

        """

        def rule(m: pyo.ConcreteModel, t: int, j: int):  # noqa: ARG001, ANN202
            previous_soc = self.param_battery_soc_initial[j] if t == 0 else self.var_battery_soc[t - 1, j]
            return (
                self.var_battery_soc[t, j]
                == previous_soc
                + self.var_battery_charge[t, j] * self.param_battery_efficiency_charging[j]  # pyright: ignore reportOperatorIssue
                - self.var_battery_discharge[t, j] / self.param_battery_efficiency_discharging[j]  # pyright: ignore reportOperatorIssue
            )

        set_time, set_batteries = self.var_battery_soc.index_set().subsets()
        if EnergyModelSetName(set_time.name) != EnergyModelSetName.TIME:
            msg = f"Expected time set, got {set_time.name} instead"
            raise ValueError(msg)
        return pyo.Constraint(
            set_time,
            set_batteries,
            rule=rule,
        )


class BatterySocBoundsConstraint(SystemConstraint):
    """Battery state of charge bounds constraint.

    This constraint ensures that battery state of charge remains within
    the physical capacity limits of the battery.
    """

    _name: ClassVar = EnergyModelConstraintName.BATTERY_SOC_BOUNDS
    var_battery_soc: pyo.Var
    param_battery_capacity: pyo.Param

    @property
    def constraint(self) -> pyo.Constraint:
        """Get the battery SOC bounds constraint.

        Returns:
            Pyomo constraint ensuring SOC stays within capacity limits.

        """

        def rule(m: pyo.ConcreteModel, t: int, j: int):  # noqa: ARG001, ANN202
            return self.var_battery_soc[t, j] <= self.param_battery_capacity[j]  # pyright: ignore reportOperatorIssue

        set_time, set_batteries = self.var_battery_soc.index_set().subsets()
        return pyo.Constraint(
            set_time,
            set_batteries,
            rule=rule,
        )


class BatterySocEndConstraint(SystemConstraint):
    """Battery terminal state of charge constraint.

    This constraint ensures that the battery reaches the specified
    terminal state of charge at the end of the optimization period.
    """

    _name: ClassVar = EnergyModelConstraintName.BATTERY_SOC_TERMINAL
    var_battery_soc: pyo.Var
    param_battery_soc_terminal: pyo.Param

    @property
    def constraint(self) -> pyo.Constraint:
        """Get the battery terminal SOC constraint.

        Returns:
            Pyomo constraint ensuring battery reaches terminal SOC.

        """

        def rule(m: pyo.ConcreteModel, j: int):  # noqa: ARG001, ANN202
            set_time, set_batteries = self.var_battery_soc.index_set().subsets()
            return self.var_battery_soc[set_time.data()[-1], j] == self.param_battery_soc_terminal[j]

        _, set_batteries = self.var_battery_soc.index_set().subsets()
        return pyo.Constraint(
            set_batteries,
            rule=rule,
        )
