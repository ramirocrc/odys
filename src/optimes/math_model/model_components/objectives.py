from abc import ABC, abstractmethod
from datetime import timedelta
from enum import Enum, unique
from typing import ClassVar

import pyomo.environ as pyo
from pydantic import BaseModel
from pyomo.common.enums import ObjectiveSense

SECONDS_IN_HOUR = 3600


@unique
class EnergyModelObjectiveName(Enum):
    MIN_OPERATIONAL_COST = "obj_minimize_operational_cost"


class SystemObjective(ABC, BaseModel, arbitrary_types_allowed=True, extra="forbid"):
    name: ClassVar

    @property
    def component(self) -> pyo.Objective:
        return self.function

    @property
    @abstractmethod
    def function(self) -> pyo.Objective:
        pass


class MinimizeOperationalCostObjective(SystemObjective):
    _name: ClassVar = EnergyModelObjectiveName.MIN_OPERATIONAL_COST
    var_generator_power: pyo.Var
    param_generator_variable_cost: pyo.Param
    param_scenario_timestep: pyo.Param

    @property
    def name(self) -> EnergyModelObjectiveName:
        return self._name

    @property
    def function(self) -> pyo.Objective:
        set_time, set_generators = self.var_generator_power.index_set().subsets()
        timestep = self.param_scenario_timestep.value  # pyright: ignore reportAttributeAccessIssue
        # todo: change parameter from timedelta to integer
        if not isinstance(timestep, timedelta):
            msg = "param_scenario_timestep must be a timedelta object"
            raise TypeError(msg)

        timestep_hours = timestep.total_seconds() / SECONDS_IN_HOUR

        def rule(m: pyo.ConcreteModel):  # noqa: ARG001, ANN202
            return sum(
                self.var_generator_power[t, i] * self.param_generator_variable_cost[i] * timestep_hours  # pyright: ignore reportOperatorIssue
                for t in set_time
                for i in set_generators
            )

        return pyo.Objective(
            rule=rule,
            sense=ObjectiveSense.minimize,
        )
