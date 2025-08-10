"""Objective function definitions for energy system optimization models.

This module defines objective function names and types used in energy system
optimization models.
"""

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
    """Enumeration of objective function names used in the energy model."""

    MIN_OPERATIONAL_COST = "obj_minimize_operational_cost"


class SystemObjective(ABC, BaseModel, arbitrary_types_allowed=True, extra="forbid"):
    """Abstract base class for system objectives.

    This class defines the interface for all objective functions in the
    energy system model, providing a common structure for objective implementation.
    """

    name: ClassVar

    @property
    def component(self) -> pyo.Objective:
        """Get the Pyomo objective component.

        Returns:
            The Pyomo objective object.

        """
        return self.function

    @property
    @abstractmethod
    def function(self) -> pyo.Objective:
        """Get the Pyomo objective function.

        This abstract method must be implemented by subclasses to
        define the specific objective function logic.

        Returns:
            The Pyomo objective object.

        """


class MinimizeOperationalCostObjective(SystemObjective):
    """Objective function to minimize operational costs.

    This objective minimizes the total operational cost of the energy system,
    considering generator variable costs and time periods.
    """

    _name: ClassVar = EnergyModelObjectiveName.MIN_OPERATIONAL_COST
    var_generator_power: pyo.Var
    param_generator_variable_cost: pyo.Param
    param_scenario_timestep: pyo.Param

    @property
    def name(self) -> EnergyModelObjectiveName:
        """Get the objective name.

        Returns:
            The objective name enum value.

        """
        return self._name

    @property
    def function(self) -> pyo.Objective:
        """Get the operational cost minimization objective.

        Returns:
            Pyomo objective function minimizing total operational costs.

        Raises:
            TypeError: If the timestep parameter is not a timedelta object.

        """
        set_time, set_generators = self.var_generator_power.index_set().subsets()
        timestep = self.param_scenario_timestep.value  # pyright: ignore reportAttributeAccessIssue
        # TODO: change parameter from timedelta to integer
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
