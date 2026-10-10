"""Base class of the model formulation of one objective term."""

from abc import ABC, abstractmethod
from typing import Self

import linopy
from pydantic import BaseModel, ConfigDict

from odys.domain.objective import Objective
from odys.optimization.constraints.constraints_group import ConstraintGroup
from odys.optimization.formulations.base import Formulation
from odys.parameters.context import ModelContext


class ObjectiveTermInputs(BaseModel):
    """What an objective term is built from: the objective, the shared indexing, and the entity formulations."""

    model_config = ConfigDict(frozen=True, extra="forbid", arbitrary_types_allowed=True)

    objective: Objective
    context: ModelContext
    formulations: tuple[Formulation, ...]


class ObjectiveTermFormulation(ConstraintGroup, ABC):
    """The optimization model of one objective term: its variables, its `@constraint` methods and its expression.

    It is built only when the objective has a term of its type. Terms read the
    profit of the entity formulations with `per_scenario_profit(self.formulations)`,
    once the formulations' variables exist.
    """

    def __init__(self, inputs: ObjectiveTermInputs) -> None:
        """Initialize with the shared indexing and the entity formulations of the problem.

        Args:
            inputs: The objective, the shared indexing, and the entity formulations.
        """
        self.context = inputs.context
        self.formulations = inputs.formulations

    @classmethod
    @abstractmethod
    def build(cls, inputs: ObjectiveTermInputs) -> Self | None:
        """Return the formulation of this type's objective term, or None if the objective has none.

        Args:
            inputs: The objective, the shared indexing, and the entity formulations.
        """

    def add_variables(self, model: linopy.Model) -> None:
        """Add this term's decision variables to the model. The default adds none.

        Args:
            model: The linopy model to add the variables to.
        """

    @abstractmethod
    def expression(self) -> linopy.LinearExpression:
        """Return the weighted term to maximize."""
