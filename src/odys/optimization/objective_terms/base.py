"""Base class of the model formulation of one objective term."""

from abc import ABC, abstractmethod
from typing import Self

import linopy
from pydantic import BaseModel, ConfigDict

from odys.domain.objective import Objective
from odys.optimization.constraints.model_constraint import ModelConstraint
from odys.optimization.formulations.base import Formulation
from odys.parameters.context import ModelContext


class ObjectiveTermInputs(BaseModel):
    """What an objective term is built from: the objective, the indexing, the model and the entity formulations."""

    model_config = ConfigDict(frozen=True, extra="forbid", arbitrary_types_allowed=True)

    objective: Objective
    context: ModelContext
    model: linopy.Model
    formulations: tuple[Formulation, ...]


class ObjectiveTermFormulation(ABC):
    """The optimization model of one objective term: its variables, its constraints and its expression.

    It is built only when the objective has a term of its type, after the entity
    formulations, and adds its variables, if any, when built. Terms read the profit
    of the entity formulations with `per_scenario_profit(self.formulations)`.
    """

    def __init__(self, inputs: ObjectiveTermInputs) -> None:
        """Initialize with the shared indexing and the entity formulations of the problem.

        Args:
            inputs: The objective, the shared indexing, the model, and the entity formulations.
        """
        self.context = inputs.context
        self.formulations = inputs.formulations

    @classmethod
    @abstractmethod
    def build(cls, inputs: ObjectiveTermInputs) -> Self | None:
        """Return the formulation of this type's objective term, or None if the objective has none.

        Args:
            inputs: The objective, the shared indexing, the model, and the entity formulations.
        """

    def constraints(self) -> list[ModelConstraint]:
        """Return the constraints of this term, in the order they are added to the model. The default is none."""
        return []

    @abstractmethod
    def expression(self) -> linopy.LinearExpression:
        """Return the weighted term to maximize."""
