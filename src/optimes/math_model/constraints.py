# pyright: reportArgumentType=none, reportCallIssue=none, reportOperatorIssue=none, reportAttributeAccessIssue=none
from abc import ABC, abstractmethod

import pyomo.environ as pyo
from pydantic import BaseModel

from optimes.assets.generator import PowerGenerator
from optimes.assets.storage import Battery
from optimes.math_model.model_enums import EnergyModelConstraint
from optimes.system.load import LoadProfile


class PyomoContraint(ABC):
    @property
    @abstractmethod
    def constraint(self) -> pyo.Constraint:
        pass

    @property
    @abstractmethod
    def name(self) -> EnergyModelConstraint:
        pass


class PowerBalanceConstraint(PyomoContraint, BaseModel, arbitrary_types_allowed=True):
    generators_set: pyo.Set
    batteries_set: pyo.Set
    generator_power: pyo.Var
    battery_discharge: pyo.Var
    battery_charge: pyo.Var
    load_profile: LoadProfile
    time_set: pyo.Set

    @property
    def name(self) -> EnergyModelConstraint:
        return EnergyModelConstraint.POWER_BALANCE

    @property
    def constraint(self) -> pyo.Constraint:
        def rule(m: pyo.ConcreteModel, t: int):
            generation_total = sum(self.generator_power[t, i] for i in self.generators_set)
            discharge_total = sum(self.battery_discharge[t, j] for j in self.batteries_set)
            charge_total = sum(self.battery_charge[t, j] for j in self.batteries_set)
            return generation_total + discharge_total == self.load_profile.profile[t] + charge_total

        return pyo.Constraint(
            self.time_set,
            rule=rule,
        )


class GenerationLimitConstraint(BaseModel, arbitrary_types_allowed=True):
    generator_power: pyo.Var
    generators: list[PowerGenerator]
    time_set: pyo.Set
    generator_set: pyo.Set

    @property
    def name(self) -> EnergyModelConstraint:
        return EnergyModelConstraint.GENERATOR_LIMIT

    @property
    def constraint(self) -> pyo.Constraint:
        def rule(m: pyo.ConcreteModel, t: int, i: int):
            return self.generator_power[t, i] <= self.generators[i].nominal_power

        return pyo.Constraint(
            self.time_set,
            self.generator_set,
            rule=rule,
        )


class BatteryChargeModeConstraint(BaseModel, arbitrary_types_allowed=True):
    battery_charge: pyo.Var
    battery_charge_mode: pyo.Var
    batteries: list[Battery]
    time_set: pyo.Set
    battery_set: pyo.Set

    @property
    def name(self) -> EnergyModelConstraint:
        return EnergyModelConstraint.BATTERY_CHARGE_LIMIT

    @property
    def constraint(self):
        def rule(m: pyo.ConcreteModel, t: int, j: int):
            max_power = self.batteries[j].max_power
            return self.battery_charge[t, j] <= max_power * self.battery_charge_mode[t, j]

        return pyo.Constraint(
            self.time_set,
            self.battery_set,
            rule=rule,
        )


class BatteryDischargeModeConstraint(BaseModel, arbitrary_types_allowed=True):
    battery_discharge: pyo.Var
    battery_charge_mode: pyo.Var
    batteries: list[Battery]
    time_set: pyo.Set
    battery_set: pyo.Set

    @property
    def name(self) -> EnergyModelConstraint:
        return EnergyModelConstraint.BATTERY_DISCHARGE_LIMIT

    @property
    def constraint(self):
        def rule(m: pyo.ConcreteModel, t: int, j: int):
            max_power = self.batteries[j].max_power
            return self.battery_discharge[t, j] <= max_power * (1 - self.battery_charge_mode[t, j])

        return pyo.Constraint(
            self.time_set,
            self.battery_set,
            rule=rule,
        )


class BatterySocDynamicsConstraint(BaseModel, arbitrary_types_allowed=True):
    battery_soc: pyo.Var
    battery_charge: pyo.Var
    battery_discharge: pyo.Var
    batteries: list[Battery]
    time_set: pyo.Set
    battery_set: pyo.Set

    @property
    def name(self) -> EnergyModelConstraint:
        return EnergyModelConstraint.BATTERY_SOC_DYNAMICS

    @property
    def constraint(self) -> pyo.Constraint:
        def rule(m: pyo.ConcreteModel, t: int, j: int):
            battery_j = self.batteries[j]
            previous_soc = battery_j.soc_start if t == 0 else self.battery_soc[t - 1, j]
            return (
                self.battery_soc[t, j]
                == previous_soc
                + self.battery_charge[t, j] * battery_j.efficiency_charging
                - self.battery_discharge[t, j] / battery_j.efficiency_discharging
            )

        return pyo.Constraint(
            self.time_set,
            self.battery_set,
            rule=rule,
        )


class BatterySocBoundsConstraint(BaseModel, arbitrary_types_allowed=True):
    battery_soc: pyo.Var
    batteries: list[Battery]
    time_set: pyo.Set
    battery_set: pyo.Set

    @property
    def name(self) -> EnergyModelConstraint:
        return EnergyModelConstraint.BATTERY_SOC_BOUNDS

    @property
    def constraint(self) -> pyo.Constraint:
        def rule(m: pyo.ConcreteModel, t: int, j: int):
            return pyo.inequality(0, self.battery_soc[t, j], self.batteries[j].capacity)

        return pyo.Constraint(
            self.time_set,
            self.battery_set,
            rule=rule,
        )


class BatterySocEndConstraint(BaseModel, arbitrary_types_allowed=True):
    battery_soc: pyo.Var
    batteries: list[Battery]
    time_set: pyo.Set
    battery_set: pyo.Set

    @property
    def name(self) -> EnergyModelConstraint:
        return EnergyModelConstraint.BATTERY_SOC_TERMINAL

    @property
    def constraint(self) -> pyo.Constraint:
        def rule(m: pyo.ConcreteModel, j: int):
            if self.batteries[j].soc_end is None:
                return pyo.Constraint.Skip

            return self.battery_soc[self.time_set.data()[-1], j] == self.batteries[j].soc_end

        return pyo.Constraint(
            self.battery_set,
            rule=rule,
        )
