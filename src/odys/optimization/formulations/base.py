"""Base class of the model formulation of one entity type."""

from abc import ABC, abstractmethod
from collections.abc import Sequence
from functools import reduce
from operator import add
from typing import ClassVar, Self, TypeVar

import linopy
import xarray as xr
from pydantic import BaseModel, ConfigDict

from odys.domain.entities.base import EnergyEntity
from odys.domain.exceptions import OdysError
from odys.optimization.constraints.constraints_group import ConstraintGroup
from odys.optimization.variable_owner import VariableOwner, VariablesT
from odys.parameters.context import ModelContext
from odys.parameters.coordinates import Coordinates

EntityT = TypeVar("EntityT", bound=EnergyEntity)
FormulationT = TypeVar("FormulationT", bound="Formulation")


class Formulation(ConstraintGroup, ABC):
    """The optimization model of every entity of one type, vectorized along that type's dimension.

    A formulation owns, for its entity type: the parameter arrays, the decision
    variables (created in `add_variables`), the `@constraint` methods (inherited
    discovery from `ConstraintGroup`), the net power it injects into the power
    balance, and its profit per scenario. It is built only when the system has
    at least one entity of its type, so its methods never check for absence.
    It holds its variables once added, so it belongs to a single model.

    Each subclass names its own axis (`dimension`) and the entity type it models
    (`entity_type`); its entities' names are the coordinates along that axis.
    """

    dimension: ClassVar[str]
    entity_type: ClassVar[type[EnergyEntity]]

    def __init__(self, entities: Sequence[EnergyEntity], context: ModelContext) -> None:
        """Initialize with this type's entities and the shared indexing of the problem.

        Args:
            entities: The entities of this formulation's type, at least one, in order.
            context: The time and scenario coordinates, step length and profiles of the problem.
        """
        self.context = context
        self.coordinates = Coordinates.of_entities(self.dimension, entities)

    @classmethod
    @abstractmethod
    def build(cls, inputs: "FormulationInputs") -> Self | None:
        """Return the formulation of this type's entities, or None if the system has none.

        Args:
            inputs: Every entity of the system, the shared indexing, and the formulations built before this one.
        """

    def add_variables(self, model: linopy.Model) -> None:
        """Add this formulation's decision variables to the model. The default adds none.

        Args:
            model: The linopy model to add the variables to.
        """

    @abstractmethod
    def power_injection(self) -> linopy.LinearExpression | xr.DataArray | None:
        """Return the net power these entities inject into the bus, per scenario and time, in MW.

        Supply is positive and demand negative. A constant array (fixed demand) has no
        decision variable. None means the entity type is outside the power balance (chargers).
        """

    def profit(self) -> linopy.LinearExpression | None:
        """Return the profit of these entities per scenario, with energy terms scaled by the step length.

        The default is None: the entity type adds nothing to the objective.
        """
        return None


class FormulationInputs(BaseModel):
    """What a formulation is built from: the system's entities, the shared indexing, and earlier formulations.

    Formulations are built in `FORMULATIONS` order, so a formulation that depends
    on another (charging on electric vehicles) finds it in `built`.
    """

    model_config = ConfigDict(frozen=True, extra="forbid", arbitrary_types_allowed=True)

    entities: tuple[EnergyEntity, ...]
    context: ModelContext
    built: tuple[Formulation, ...] = ()

    def of_type(self, kind: type[EntityT]) -> list[EntityT]:
        """Return the entities of the given type, in order."""
        return [entity for entity in self.entities if isinstance(entity, kind)]

    def formulation_of(self, kind: type[FormulationT]) -> FormulationT | None:
        """Return an already built formulation of the given type, if any."""
        return next((formulation for formulation in self.built if isinstance(formulation, kind)), None)


class VariableFormulation(VariableOwner[VariablesT], Formulation):
    """An entity formulation with decision variables, held in a typed, frozen variables object (see `VariableOwner`)."""


def per_scenario_profit(formulations: Sequence[Formulation]) -> linopy.LinearExpression:
    """Return the profit per scenario: every formulation's profit, summed over time and entities.

    Scenario probabilities are not applied; the expected-profit and CVaR terms do that.

    Args:
        formulations: The formulations of the problem, whose variables are already added.

    Raises:
        OdysError: If no formulation contributes a profit term.
    """
    profits = [profit for formulation in formulations if (profit := formulation.profit()) is not None]
    if not profits:
        msg = "The problem has no entity type that contributes a profit term."
        raise OdysError(msg)
    total: linopy.LinearExpression = reduce(add, profits)
    return total
