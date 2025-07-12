# pyright: reportArgumentType=none, reportCallIssue=none, reportOperatorIssue=none, reportAttributeAccessIssue=none

import pyomo.environ as pyo
from pyomo.common.enums import ObjectiveSense

from optimes.assets.generator import PowerGenerator


def minimize_operational_cost_of(
    generator_power: pyo.Var,
    generators: list[PowerGenerator],
):
    set_time, set_generators = generator_power.index_set().subsets()

    def rule(m: pyo.ConcreteModel):
        return sum(generator_power[t, i] * generators[i].variable_cost for t in set_time for i in set_generators)

    return pyo.Objective(
        rule=rule,
        sense=ObjectiveSense.minimize,
    )
