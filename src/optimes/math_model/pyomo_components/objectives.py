# pyright: reportArgumentType=none, reportCallIssue=none, reportOperatorIssue=none, reportAttributeAccessIssue=none

from abc import ABC, abstractmethod
from enum import Enum, unique
from typing import ClassVar

import pyomo.environ as pyo
from pydantic import BaseModel
from pyomo.common.enums import ObjectiveSense


@unique
class EnergyModelObjectiveName(Enum):
    MIN_OPERATIONAL_COST = "obj_minimize_operational_cost"


class PyomoObjective(ABC, BaseModel, arbitrary_types_allowed=True, extra="forbid"):
    name: ClassVar

    @property
    def component(self) -> pyo.Objective:
        return self.function

    @property
    @abstractmethod
    def function(self) -> pyo.Objective:
        pass


class MinimizeOperationalCostObjective(PyomoObjective):
    name: ClassVar = EnergyModelObjectiveName.MIN_OPERATIONAL_COST
    var_generator_power: pyo.Var
    param_generator_variable_cost: pyo.Param

    @property
    def function(self) -> pyo.Objective:
        set_time, set_generators = self.var_generator_power.index_set().subsets()

        def rule(m: pyo.ConcreteModel):  # noqa: ARG001, ANN202
            return sum(
                self.var_generator_power[t, i] * self.param_generator_variable_cost[i]
                for t in set_time
                for i in set_generators
            )

        return pyo.Objective(
            rule=rule,
            sense=ObjectiveSense.minimize,
        )
