"""Everything needed to build the optimization model of one energy system."""

from collections.abc import Sequence
from typing import Self, TypeVar

import xarray as xr
from pydantic import BaseModel, ConfigDict

from odys.domain.entities.base import EnergyEntity
from odys.domain.horizon import Horizon
from odys.domain.objective import Objective
from odys.domain.scenario import ScenarioSet
from odys.optimization.formulations import FORMULATIONS
from odys.optimization.formulations.base import Formulation, FormulationInputs
from odys.optimization.objective_terms import OBJECTIVE_TERM_FORMULATIONS
from odys.optimization.objective_terms.base import ObjectiveTermFormulation, ObjectiveTermInputs
from odys.parameters.context import ModelContext
from odys.results.dispatch import Dispatch

FormulationT = TypeVar("FormulationT", bound=Formulation)


class OptimizationProblem(BaseModel):
    """The input of the model builder for one energy system.

    It holds the shared indexing, one formulation per entity type present in the
    system, and one formulation per objective term.
    Formulations keep the variables of the model they are built into, so a
    problem is built into one model only; call `EnergySystem.build_problem()`
    again for another model.
    """

    model_config = ConfigDict(frozen=True, extra="forbid", arbitrary_types_allowed=True)

    context: ModelContext
    formulations: tuple[Formulation, ...]
    objective_terms: tuple[ObjectiveTermFormulation, ...]

    @classmethod
    def assemble(
        cls,
        entities: Sequence[EnergyEntity],
        horizon: Horizon,
        scenario_set: ScenarioSet,
        objective: Objective,
    ) -> Self:
        """Build the shared indexing and the formulations of the entity types present and of the objective's terms.

        Entity formulations are built in `FORMULATIONS` order, each seeing the ones
        built before it; objective terms in `OBJECTIVE_TERM_FORMULATIONS` order.

        Args:
            entities: Every asset and market of the system.
            horizon: The time grid of the optimization.
            scenario_set: The scenarios of the problem.
            objective: The objective to maximize.

        Returns:
            The problem, ready for the model builder.
        """
        context = ModelContext(horizon=horizon, scenario_set=scenario_set)
        all_entities = tuple(entities)
        formulations: tuple[Formulation, ...] = ()
        for formulation_type in FORMULATIONS:
            inputs = FormulationInputs(entities=all_entities, context=context, built=formulations)
            formulation = formulation_type.build(inputs)
            if formulation is not None:
                formulations = (*formulations, formulation)
        term_inputs = ObjectiveTermInputs(objective=objective, context=context, formulations=formulations)
        objective_terms = tuple(
            term for term_type in OBJECTIVE_TERM_FORMULATIONS if (term := term_type.build(term_inputs)) is not None
        )
        return cls(context=context, formulations=formulations, objective_terms=objective_terms)

    def formulation_of(self, kind: type[FormulationT]) -> FormulationT | None:
        """Return the formulation of the given type, if the system has entities of that type.

        Args:
            kind: The formulation type, such as `FlexibleLoadFormulation`.

        Returns:
            The formulation, or None if the system has no entity of that type.

        """
        return next((formulation for formulation in self.formulations if isinstance(formulation, kind)), None)

    def dispatches(self, solution: xr.Dataset) -> tuple[Dispatch, ...]:
        """Return the dispatch results of every entity type that has them, read from the solution of the model.

        Args:
            solution: The solution of the model built from this problem, by linopy variable name.
        """
        return tuple(
            dispatch for formulation in self.formulations if (dispatch := formulation.dispatch(solution)) is not None
        )
