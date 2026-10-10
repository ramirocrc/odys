"""The decision variables of one part of the model, created once and typed."""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

import linopy
from pydantic import BaseModel

from odys.domain.exceptions import OdysError

VariablesT = TypeVar("VariablesT", bound=BaseModel)


class VariableOwner(ABC, Generic[VariablesT]):
    """A part of the model that holds its decision variables in a typed, frozen variables object.

    The variables are created once, in `add_variables`, and belong to that one
    model: a second `add_variables` raises, so a problem is built into one model only.
    Entity formulations and objective terms with variables both use it. List it
    before the formulation base class, whose `add_variables` adds nothing.
    """

    _variables: VariablesT | None = None

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
        """Add the decision variables to the model.

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
