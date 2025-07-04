# pyright: reportArgumentType=none, reportCallIssue=none, reportOperatorIssue=none, reportAttributeAccessIssue=none

import pyomo.environ as pyo
from pyomo.common.enums import ObjectiveSense

from optimes.assets.generator import PowerGenerator


def minimize_operational_cost_of(
    generator_power: pyo.Var,
    time_set: pyo.Set,
    generators_set: pyo.Set,
    generators: list[PowerGenerator],
):
    def rule(m: pyo.ConcreteModel):
        return sum(generator_power[t, i] * generators[i].variable_cost for t in time_set for i in generators_set)

    return pyo.Objective(
        rule=rule,
        sense=ObjectiveSense.minimize,
    )
