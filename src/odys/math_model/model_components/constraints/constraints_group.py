"""Constraint group base class for organizing related model constraints."""

from abc import ABC, abstractmethod

from odys.math_model.milp_model import EnergyMILPModel
from odys.math_model.model_components.constraints.model_constraint import ModelConstraint


class ConstraintGroup(ABC):
    """Base class for grouping related model constraints."""

    @abstractmethod
    def __init__(self, milp_model: EnergyMILPModel) -> None:
        """Initialize with the MILP model."""

    @property
    @abstractmethod
    def all(self) -> tuple[ModelConstraint, ...]:
        """Return a tuple of model constraints."""
