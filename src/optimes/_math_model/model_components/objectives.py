"""Objective function definitions for energy system optimization models.

This module defines objective function names and types used in energy system
optimization models.
"""

from abc import ABC, abstractmethod
from enum import Enum, unique
from typing import ClassVar

import linopy
import xarray as xr
from pydantic import BaseModel

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
    @abstractmethod
    def function(self) -> linopy.LinearExpression:
        """Get the Pyomo objective function.

        This abstract method must be implemented by subclasses to
        define the specific objective function logic.

        Returns:
            The Pyomo objective object.

        """


class LinopyMinimizeOperationalCostObjective(SystemObjective):
    """Objective function to minimize operational costs.

    This objective minimizes the total operational cost of the energy system,
    considering generator variable costs and time periods.
    """

    _name: ClassVar = EnergyModelObjectiveName.MIN_OPERATIONAL_COST
    var_generator_power: linopy.Variable
    param_generator_variable_cost: xr.DataArray

    @property
    def name(self) -> EnergyModelObjectiveName:
        """Get the objective name.

        Returns:
            The objective name enum value.

        """
        return self._name

    @property
    def function(self) -> linopy.LinearExpression:
        """Get the operational cost minimization objective.

        Returns:
            Pyomo objective function minimizing total operational costs.

        Raises:
            TypeError: If the timestep parameter is not a timedelta object.

        """
        return self.var_generator_power * self.param_generator_variable_cost  # pyright: ignore reportOperatorIssue
