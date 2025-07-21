# pyright: reportArgumentType=none, reportCallIssue=none, reportOperatorIssue=none, reportAttributeAccessIssue=none
from abc import ABC, abstractmethod
from enum import Enum, unique
from typing import ClassVar

import pyomo.environ as pyo
from pydantic import BaseModel

from optimes.math_model.model_components.sets import EnergyModelSetName


@unique
class EnergyModelConstraintName(Enum):
    POWER_BALANCE = "const_power_balance"
    GENERATOR_LIMIT = "const_generator_limit"
    BATTERY_CHARGE_LIMIT = "const_battery_charge_limit"
    BATTERY_DISCHARGE_LIMIT = "const_battery_discharge_limit"
    BATTERY_SOC_DYNAMICS = "const_battery_soc_dynamics"
    BATTERY_SOC_BOUNDS = "const_battery_soc_bounds"
    BATTERY_SOC_TERMINAL = "const_battery_soc_terminal"


class SystemConstraint(ABC, BaseModel, arbitrary_types_allowed=True, extra="forbid"):
    name: ClassVar[EnergyModelConstraintName]

    @property
    def component(self) -> pyo.Constraint:
        return self.constraint

    @property
    @abstractmethod
    def constraint(self) -> pyo.Constraint:
        pass


class PowerBalanceConstraint(SystemConstraint):
    name: ClassVar = EnergyModelConstraintName.POWER_BALANCE
    var_generator_power: pyo.Var
    var_battery_discharge: pyo.Var
    var_battery_charge: pyo.Var
    param_demand: pyo.Param

    @property
    def constraint(self) -> pyo.Constraint:
        def rule(m: pyo.ConcreteModel, t: int):  # noqa: ARG001, ANN202
            generation_total = sum(self.var_generator_power[t, i] for i in set_generator)
            discharge_total = sum(self.var_battery_discharge[t, j] for j in set_batteries)
            charge_total = sum(self.var_battery_charge[t, j] for j in set_batteries)
            return generation_total + discharge_total == self.param_demand[t] + charge_total

        set_time, set_generator = self.var_generator_power.index_set().subsets()
        _, set_batteries = self.var_battery_discharge.index_set().subsets()
        return pyo.Constraint(
            set_time,
            rule=rule,
        )


class GenerationLimitConstraint(SystemConstraint):
    name: ClassVar = EnergyModelConstraintName.GENERATOR_LIMIT
    var_generator_power: pyo.Var
    param_generator_nominal_power: pyo.Param

    @property
    def constraint(self) -> pyo.Constraint:
        def rule(m: pyo.ConcreteModel, t: int, i: int):  # noqa: ARG001, ANN202
            return self.var_generator_power[t, i] <= self.param_generator_nominal_power[i]

        set_time, set_generator = self.var_generator_power.index_set().subsets()
        return pyo.Constraint(
            set_time,
            set_generator,
            rule=rule,
        )


class BatteryChargeModeConstraint(SystemConstraint):
    name: ClassVar = EnergyModelConstraintName.BATTERY_CHARGE_LIMIT
    var_battery_charge: pyo.Var
    var_battery_charge_mode: pyo.Var
    param_battery_max_power: pyo.Param

    @property
    def constraint(self) -> pyo.Constraint:
        def rule(m: pyo.ConcreteModel, t: int, j: int):  # noqa: ARG001, ANN202
            return self.var_battery_charge[t, j] <= self.param_battery_max_power[j] * self.var_battery_charge_mode[t, j]

        set_time, set_batteries = self.var_battery_charge.index_set().subsets()
        return pyo.Constraint(
            set_time,
            set_batteries,
            rule=rule,
        )


class BatteryDischargeModeConstraint(SystemConstraint):
    name: ClassVar = EnergyModelConstraintName.BATTERY_DISCHARGE_LIMIT
    var_battery_discharge: pyo.Var
    var_battery_charge_mode: pyo.Var
    param_battery_max_power: pyo.Param

    @property
    def constraint(self) -> pyo.Constraint:
        def rule(m: pyo.ConcreteModel, t: int, j: int):  # noqa: ARG001, ANN202
            return self.var_battery_discharge[t, j] <= self.param_battery_max_power[j] * (
                1 - self.var_battery_charge_mode[t, j]
            )

        set_time, set_batteries = self.var_battery_discharge.index_set().subsets()
        return pyo.Constraint(
            set_time,
            set_batteries,
            rule=rule,
        )


class BatterySocDynamicsConstraint(SystemConstraint):
    name: ClassVar = EnergyModelConstraintName.BATTERY_SOC_DYNAMICS
    var_battery_soc: pyo.Var
    var_battery_charge: pyo.Var
    var_battery_discharge: pyo.Var
    param_battery_efficiency_charging: pyo.Param
    param_battery_efficiency_discharging: pyo.Param
    param_battery_soc_initial: pyo.Param

    @property
    def constraint(self) -> pyo.Constraint:
        def rule(m: pyo.ConcreteModel, t: int, j: int):  # noqa: ARG001, ANN202
            previous_soc = self.param_battery_soc_initial[j] if t == 0 else self.var_battery_soc[t - 1, j]
            return (
                self.var_battery_soc[t, j]
                == previous_soc
                + self.var_battery_charge[t, j] * self.param_battery_efficiency_charging[j]
                - self.var_battery_discharge[t, j] / self.param_battery_efficiency_discharging[j]
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
    name: ClassVar = EnergyModelConstraintName.BATTERY_SOC_BOUNDS
    var_battery_soc: pyo.Var
    param_battery_capacity: pyo.Param

    @property
    def constraint(self) -> pyo.Constraint:
        def rule(m: pyo.ConcreteModel, t: int, j: int):  # noqa: ARG001, ANN202
            return pyo.inequality(0, self.var_battery_soc[t, j], self.param_battery_capacity[j])

        set_time, set_batteries = self.var_battery_soc.index_set().subsets()
        return pyo.Constraint(
            set_time,
            set_batteries,
            rule=rule,
        )


class BatterySocEndConstraint(SystemConstraint):
    name: ClassVar = EnergyModelConstraintName.BATTERY_SOC_TERMINAL
    var_battery_soc: pyo.Var
    param_battery_soc_terminal: pyo.Param

    @property
    def constraint(self) -> pyo.Constraint:
        set_time, set_batteries = self.var_battery_soc.index_set().subsets()

        def rule(m: pyo.ConcreteModel, j: int):  # noqa: ARG001, ANN202
            return self.var_battery_soc[set_time.data()[-1], j] == self.param_battery_soc_terminal[j]

        return pyo.Constraint(
            set_batteries,
            rule=rule,
        )
