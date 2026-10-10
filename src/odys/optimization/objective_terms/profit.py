"""The expected-profit objective term."""

from typing import Self

import linopy

from odys.domain.objective import ProfitTerm
from odys.optimization.formulations.base import per_scenario_profit
from odys.optimization.objective_terms.base import ObjectiveTermFormulation, ObjectiveTermInputs
from odys.parameters.dimensions import ModelDimension


class ProfitTermFormulation(ObjectiveTermFormulation):
    """Expected profit: the probability-weighted sum of every scenario's profit, times the term's weight."""

    def __init__(self, term: ProfitTerm, inputs: ObjectiveTermInputs) -> None:
        """Initialize the term.

        Args:
            term: The profit term of the objective.
            inputs: The objective, the shared indexing, and the entity formulations.
        """
        super().__init__(inputs)
        self.term = term

    @classmethod
    def build(cls, inputs: ObjectiveTermInputs) -> Self | None:
        """Return the profit term's formulation, or None if the objective has no profit term."""
        term = inputs.objective.term_of(ProfitTerm)
        return None if term is None else cls(term, inputs)

    def expression(self) -> linopy.LinearExpression:
        """Return the weight times Σ_s probability_s · profit_s."""
        profit = per_scenario_profit(self.formulations)
        expected_profit = (profit * self.context.probabilities).sum(ModelDimension.Scenarios)
        weighted: linopy.LinearExpression = self.term.weight * expected_profit
        return weighted
