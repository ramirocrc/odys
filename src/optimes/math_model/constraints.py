# pyright: reportArgumentType=none, reportCallIssue=none, reportOperatorIssue=none, reportAttributeAccessIssue=none
import pyomo.environ as pyo
from pydantic import BaseModel

from optimes.assets.generator import PowerGenerator
from optimes.assets.storage import Battery
from optimes.system.load import LoadProfile


class PowerBalanceConstraintParams(BaseModel, arbitrary_types_allowed=True):
    generators_set: pyo.Set
    batteries_set: pyo.Set
    generator_power: pyo.Var
    battery_discharge: pyo.Var
    battery_charge: pyo.Var
    load_profile: LoadProfile
    time_set: pyo.Set


def power_balance_constraint(params: PowerBalanceConstraintParams) -> pyo.Constraint:
    def rule(m: pyo.ConcreteModel, t: int):
        generation_total = sum(params.generator_power[t, i] for i in params.generators_set)
        discharge_total = sum(params.battery_discharge[t, j] for j in params.batteries_set)
        charge_total = sum(params.battery_charge[t, j] for j in params.batteries_set)
        return generation_total + discharge_total == params.load_profile.profile[t] + charge_total

    return pyo.Constraint(
        params.time_set,
        rule=rule,
    )


class GenerationLimitConstraintParams(BaseModel, arbitrary_types_allowed=True):
    generator_power: pyo.Var
    generators: list[PowerGenerator]
    time_set: pyo.Set
    generator_set: pyo.Set


def generation_limit_constraint(params: GenerationLimitConstraintParams) -> pyo.Constraint:
    def rule(m: pyo.ConcreteModel, t: int, i: int):
        return params.generator_power[t, i] <= params.generators[i].nominal_power

    return pyo.Constraint(
        params.time_set,
        params.generator_set,
        rule=rule,
    )


class BatteryChargeModeConstraintParams(BaseModel, arbitrary_types_allowed=True):
    battery_charge: pyo.Var
    battery_charge_mode: pyo.Var
    batteries: list[Battery]
    time_set: pyo.Set
    battery_set: pyo.Set


def battery_charge_limit_constraint(params: BatteryChargeModeConstraintParams):
    def rule(m: pyo.ConcreteModel, t: int, j: int):
        max_power = params.batteries[j].max_power
        return params.battery_charge[t, j] <= max_power * params.battery_charge_mode[t, j]

    return pyo.Constraint(
        params.time_set,
        params.battery_set,
        rule=rule,
    )


class BatteryDischargeModeConstraintParams(BaseModel, arbitrary_types_allowed=True):
    battery_discharge: pyo.Var
    battery_charge_mode: pyo.Var
    batteries: list[Battery]
    time_set: pyo.Set
    battery_set: pyo.Set


def battery_discharge_limit_constraint(params: BatteryDischargeModeConstraintParams):
    def rule(m: pyo.ConcreteModel, t: int, j: int):
        max_power = params.batteries[j].max_power
        return params.battery_discharge[t, j] <= max_power * (1 - params.battery_charge_mode[t, j])

    return pyo.Constraint(
        params.time_set,
        params.battery_set,
        rule=rule,
    )


class BatterySocDynamicsConstraintParams(BaseModel, arbitrary_types_allowed=True):
    battery_soc: pyo.Var
    battery_charge: pyo.Var
    battery_discharge: pyo.Var
    batteries: list[Battery]
    time_set: pyo.Set
    battery_set: pyo.Set


def battery_soc_dynamics_constraint(params: BatterySocDynamicsConstraintParams) -> pyo.Constraint:
    def rule(m: pyo.ConcreteModel, t: int, j: int):
        battery_j = params.batteries[j]
        previous_soc = battery_j.soc_start if t == 0 else params.battery_soc[t - 1, j]
        return (
            params.battery_soc[t, j]
            == previous_soc
            + params.battery_charge[t, j] * battery_j.efficiency_charging
            - params.battery_discharge[t, j] / battery_j.efficiency_discharging
        )

    return pyo.Constraint(
        params.time_set,
        params.battery_set,
        rule=rule,
    )


class BatterySocBoundsConstraintParams(BaseModel, arbitrary_types_allowed=True):
    battery_soc: pyo.Var
    batteries: list[Battery]
    time_set: pyo.Set
    battery_set: pyo.Set


def battery_soc_bounds_constraint(params: BatterySocBoundsConstraintParams) -> pyo.Constraint:
    def rule(m: pyo.ConcreteModel, t: int, j: int):
        return pyo.inequality(0, params.battery_soc[t, j], params.batteries[j].capacity)

    return pyo.Constraint(
        params.time_set,
        params.battery_set,
        rule=rule,
    )


class BatterySocEndConstraintParams(BaseModel, arbitrary_types_allowed=True):
    battery_soc: pyo.Var
    batteries: list[Battery]
    time_set: pyo.Set
    battery_set: pyo.Set


def battery_soc_terminal_constraint(params: BatterySocEndConstraintParams) -> pyo.Constraint:
    def rule(m: pyo.ConcreteModel, j: int):
        if params.batteries[j].soc_end is None:
            return pyo.Constraint.Skip

        return params.battery_soc[params.time_set.data()[-1], j] == params.batteries[j].soc_end

    return pyo.Constraint(
        params.battery_set,
        rule=rule,
    )
