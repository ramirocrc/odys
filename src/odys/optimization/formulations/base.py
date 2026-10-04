"""Base class of the model formulation of one entity type."""

from abc import ABC, abstractmethod
from typing import Generic, Self, TypeVar

import linopy
import xarray as xr
from pydantic import BaseModel, ConfigDict

from odys.domain.entities.base import EnergyEntity
from odys.domain.exceptions import OdysError
from odys.optimization.constraints.constraints_group import ConstraintGroup
from odys.parameters.context import ModelContext

VariablesT = TypeVar("VariablesT", bound=BaseModel)
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
    """

    def __init__(self, context: ModelContext) -> None:
        """Initialize with the shared indexing of the problem.

        Args:
            context: The coordinates, step length and profiles of the problem.
        """
        self.context = context

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


class VariableFormulation(Formulation, Generic[VariablesT]):
    """A formulation with decision variables, held in a typed, frozen variables object.

    The variables are created once, in `add_variables`, and belong to that one
    model: a second `add_variables` raises, so a problem is built into one model only.
    """

    def __init__(self, context: ModelContext) -> None:
        """Initialize with the shared indexing of the problem; the variables come later.

        Args:
            context: The coordinates, step length and profiles of the problem.
        """
        super().__init__(context)
        self._variables: VariablesT | None = None

    @property
    def variables(self) -> VariablesT:
        """Return the decision variables.

        Raises:
            OdysError: If `add_variables` has not run yet.
        """
        if self._variables is None:
            msg = f"{type(self).__name__}.add_variables must run before its variables are used."
            raise OdysError(msg)
        return self._variables

    def add_variables(self, model: linopy.Model) -> None:
        """Add this formulation's decision variables to the model.

        Args:
            model: The linopy model to add the variables to.

        Raises:
            OdysError: If the variables were already added to a model; build a new problem for each model.
        """
        if self._variables is not None:
            msg = f"{type(self).__name__} already has variables; build a new problem for each model."
            raise OdysError(msg)
        self._variables = self._create_variables(model)

    @abstractmethod
    def _create_variables(self, model: linopy.Model) -> VariablesT:
        """Add the decision variables to the model and return them as the typed variables object."""
