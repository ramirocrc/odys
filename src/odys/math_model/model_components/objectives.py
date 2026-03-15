"""Objective function definitions for energy system optimization models.

This module defines objective function names and types used in energy system
optimization models.
"""

import linopy

from odys.math_model.milp_model import EnergyMILPModel
from odys.math_model.model_components.sets import ModelDimension


class ObjectiveFunction:
    """Builds the objective function for the energy system optimization model."""

    def __init__(self, milp_model: EnergyMILPModel) -> None:
        """Initialize with the MILP model to build the objective from."""
        self._model = milp_model

    def profit_term(self) -> linopy.LinearExpression:
        """Build the profit expression."""
        scenario_probability = self._model.parameters.scenarios.scenario_probabilities
        return (self._model.per_scenario_profit() * scenario_probability).sum(ModelDimension.Scenarios)

    def cvar_term(self) -> linopy.LinearExpression:
        """Build the CVaR expression: η - 1/(1-alpha) * Σ_s p_s * z_s."""
        confidence_level = self._model.parameters.cvar_config.confidence_level  # type: ignore[union-attr]
        probs = self._model.parameters.scenarios.scenario_probabilities
        expected_shortfall = (probs * self._model.cvar_shortfall).sum(ModelDimension.Scenarios)
        return self._model.cvar_value_at_risk - (1 / (1 - confidence_level)) * expected_shortfall


def build_objective(milp_model: EnergyMILPModel) -> linopy.LinearExpression:
    """Build the full objective function, including the CVaR term if configured."""
    obj_fn = ObjectiveFunction(milp_model)
    objective = obj_fn.profit_term()

    cvar_config = milp_model.parameters.cvar_config

    if cvar_config is None:
        return objective

    return objective + cvar_config.weight * obj_fn.cvar_term()
