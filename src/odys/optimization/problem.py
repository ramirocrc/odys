"""Everything needed to build the optimization model of one energy system."""

from functools import reduce
from operator import add
from typing import TypeVar

import linopy
from pydantic import BaseModel, ConfigDict

from odys.domain.exceptions import OdysError
from odys.domain.objective import Objective
from odys.optimization.formulations.base import Formulation
from odys.parameters.context import ModelContext
from odys.parameters.energy_system_parameters import EnergySystemParameters

FormulationT = TypeVar("FormulationT", bound=Formulation)


class OptimizationProblem(BaseModel):
    """The input of the model builder for one energy system.

    It holds one formulation per entity type present in the system, and the
    remaining legacy parameters (the context and the objective, until the
    objective terms become formulations).
    Formulations keep the variables of the model they are built into, so a
    problem is built into one model only; call `EnergySystem.build_problem()`
    again for another model.
    """

    model_config = ConfigDict(frozen=True, extra="forbid", arbitrary_types_allowed=True)

    legacy: EnergySystemParameters
    formulations: tuple[Formulation, ...] = ()

    @property
    def context(self) -> ModelContext:
        """Return the shared indexing of the problem."""
        return self.legacy.context

    @property
    def objective(self) -> Objective:
        """Return the objective to maximize."""
        return self.legacy.objective

    def formulation_of(self, kind: type[FormulationT]) -> FormulationT | None:
        """Return the formulation of the given type, if the system has entities of that type.

        Args:
            kind: The formulation type, such as `FlexibleLoadFormulation`.

        Returns:
            The formulation, or None if the system has no entity of that type.

        """
        return next((formulation for formulation in self.formulations if isinstance(formulation, kind)), None)

    def per_scenario_profit(self) -> linopy.LinearExpression:
        """Return the profit per scenario: every formulation's profit, summed over time and entities.

        Scenario probabilities are not applied; the expected-profit and CVaR terms do that.

        Raises:
            OdysError: If no formulation contributes a profit term.
        """
        profits = [profit for formulation in self.formulations if (profit := formulation.profit()) is not None]
        if not profits:
            msg = "The problem has no entity type that contributes a profit term."
            raise OdysError(msg)
        total: linopy.LinearExpression = reduce(add, profits)
        return total
