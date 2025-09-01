"""Constraint definitions for energy system optimization models.

This module defines constraint names and types used in energy system
optimization models.
"""

from abc import ABC, abstractmethod
from typing import ClassVar

import linopy
from pydantic import BaseModel

from optimes._math_model.model_components.constraints.constraint_names import EnergyModelConstraintName


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
    @abstractmethod
    def constraint(self) -> linopy.Constraint:
        """Get the Pyomo constraint.

        This abstract method must be implemented by subclasses to
        define the specific constraint logic.

        Returns:
            The Pyomo constraint object.

        """
