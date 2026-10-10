"""The Conditional Value at Risk (CVaR) objective term."""

from typing import ClassVar, Self

import linopy
import numpy as np
from pydantic import BaseModel, ConfigDict

from odys.domain.objective import CVaRTerm
from odys.optimization.constraints.constraints_group import constraint
from odys.optimization.constraints.model_constraint import ModelConstraint
from odys.optimization.formulations.base import per_scenario_profit
from odys.optimization.objective_terms.base import ObjectiveTermFormulation, ObjectiveTermInputs
from odys.optimization.variable_owner import VariableOwner
from odys.parameters.dimensions import ModelDimension


class CVaRVariables(BaseModel):
    """Decision variables of the CVaR term: the value at risk and each scenario's shortfall below it."""

    model_config = ConfigDict(frozen=True, extra="forbid", arbitrary_types_allowed=True)

    value_at_risk: linopy.Variable
    shortfall: linopy.Variable


class CVaRTermFormulation(VariableOwner[CVaRVariables], ObjectiveTermFormulation):
    """CVaR of the profit: the value at risk less the expected shortfall below it, scaled to the tail.

    CVaR = value_at_risk - 1 / (1 - confidence_level) * sum_s probability_s * shortfall_s,
    with shortfall_s >= value_at_risk - profit_s and shortfall_s >= 0.
    """

    value_at_risk_name: ClassVar[str] = "cvar_value_at_risk"
    shortfall_name: ClassVar[str] = "cvar_shortfall"

    def __init__(self, term: CVaRTerm, inputs: ObjectiveTermInputs) -> None:
        """Initialize the term.

        Args:
            term: The CVaR term of the objective.
            inputs: The objective, the shared indexing, and the entity formulations.
        """
        super().__init__(inputs)
        self.term = term

    @classmethod
    def build(cls, inputs: ObjectiveTermInputs) -> Self | None:
        """Return the CVaR term's formulation, or None if the objective has no CVaR term."""
        term = inputs.objective.term_of(CVaRTerm)
        return None if term is None else cls(term, inputs)

    def _create_variables(self, model: linopy.Model) -> CVaRVariables:
        return CVaRVariables(
            value_at_risk=model.add_variables(name=self.value_at_risk_name, coords={}, lower=-np.inf),
            shortfall=model.add_variables(
                name=self.shortfall_name,
                coords=self.context.scenarios.dimension_coordinates_map,
                lower=0.0,
            ),
        )

    @constraint
    def _get_shortfall_constraint(self) -> ModelConstraint:
        """Each scenario's shortfall is at least the value at risk less that scenario's profit."""
        profit = per_scenario_profit(self.formulations)
        return ModelConstraint(
            constraint=self.variables.shortfall >= self.variables.value_at_risk - profit,
            name="cvar_shortfall_constraint",
        )

    def expression(self) -> linopy.LinearExpression:
        """Return the weight times the CVaR: value at risk less the tail-scaled expected shortfall."""
        expected_shortfall = (self.context.probabilities * self.variables.shortfall).sum(ModelDimension.Scenarios)
        tail_scale = 1 / (1 - self.term.confidence_level)
        weighted: linopy.LinearExpression = self.term.weight * (
            self.variables.value_at_risk - tail_scale * expected_shortfall
        )
        return weighted
