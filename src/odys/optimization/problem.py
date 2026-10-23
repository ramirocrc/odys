"""The optimization model of one energy system, with the formulations that built it."""

from collections.abc import Sequence
from functools import reduce
from operator import add
from typing import Self, TypeVar

import linopy
import xarray as xr
from pydantic import BaseModel, ConfigDict

from odys.domain.conditions import ConditionSet
from odys.domain.entities.base import EnergyEntity
from odys.domain.horizon import Horizon
from odys.domain.objective import Objective
from odys.domain.scenario import ScenarioSet
from odys.optimization.formulations import FORMULATIONS
from odys.optimization.formulations.base import Formulation, FormulationInputs
from odys.optimization.objective_terms import OBJECTIVE_TERM_FORMULATIONS
from odys.optimization.objective_terms.base import ObjectiveTermFormulation, ObjectiveTermInputs
from odys.optimization.power_balance import PowerBalance
from odys.parameters.context import ModelContext
from odys.results.dispatch import Dispatch

FormulationT = TypeVar("FormulationT", bound=Formulation)


class OptimizationProblem(BaseModel):
    """The optimization model of one energy system, ready for solving, with the formulations that built it.

    It holds the shared indexing, one formulation per entity type present in the
    system, one formulation per objective term, and the linopy model they were
    built into. Call `EnergySystem.build_problem()` again for another model.
    """

    model_config = ConfigDict(frozen=True, extra="forbid", arbitrary_types_allowed=True)

    context: ModelContext
    formulations: tuple[Formulation, ...]
    objective_terms: tuple[ObjectiveTermFormulation, ...]
    model: linopy.Model

    @classmethod
    def assemble(
        cls,
        entities: Sequence[EnergyEntity],
        horizon: Horizon,
        scenario_set: ScenarioSet,
        condition_set: ConditionSet,
        objective: Objective,
    ) -> Self:
        """Build the model: every formulation and objective term with its variables, then the constraints and objective.

        Entity formulations are built in `FORMULATIONS` order, each adding its variables
        and seeing the ones built before it; objective terms in `OBJECTIVE_TERM_FORMULATIONS`
        order. The constraints and the objective come after every variable.

        Args:
            entities: Every asset and market of the system.
            horizon: The time grid of the optimization.
            scenario_set: The scenarios of the problem.
            condition_set: The initial and final conditions of the run.
            objective: The objective to maximize.

        Returns:
            The problem, whose model is ready for solving.
        """
        context = ModelContext(horizon=horizon, scenario_set=scenario_set, condition_set=condition_set)
        model = linopy.Model(force_dim_names=True)
        all_entities = tuple(entities)
        formulations: tuple[Formulation, ...] = ()
        for formulation_type in FORMULATIONS:
            inputs = FormulationInputs(entities=all_entities, context=context, model=model, built=formulations)
            formulation = formulation_type.build(inputs)
            if formulation is not None:
                formulations = (*formulations, formulation)
        term_inputs = ObjectiveTermInputs(objective=objective, context=context, model=model, formulations=formulations)
        objective_terms = tuple(
            term for term_type in OBJECTIVE_TERM_FORMULATIONS if (term := term_type.build(term_inputs)) is not None
        )
        _add_constraints_and_objective(model, formulations, objective_terms)
        return cls(context=context, formulations=formulations, objective_terms=objective_terms, model=model)

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


def _add_constraints_and_objective(
    model: linopy.Model,
    formulations: Sequence[Formulation],
    objective_terms: Sequence[ObjectiveTermFormulation],
) -> None:
    """Add the constraints (entity formulations, the power balance, objective terms) and the maximized objective."""
    constraints = [
        *(constraint for formulation in formulations for constraint in formulation.constraints()),
        *PowerBalance(formulations).constraints(),
        *(constraint for term in objective_terms for constraint in term.constraints()),
    ]
    for constraint in constraints:
        model.add_constraints(constraint.constraint, name=constraint.name)
    objective: linopy.LinearExpression = reduce(add, (term.expression() for term in objective_terms))
    model.add_objective(objective, sense="max")
