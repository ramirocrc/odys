"""CVaR (Conditional Value at Risk) constraints for stochastic optimization."""

from __future__ import annotations

from typing import TYPE_CHECKING

from odys.optimization.constraints.constraints_group import ConstraintGroup, constraint
from odys.optimization.constraints.model_constraint import ModelConstraint

if TYPE_CHECKING:
    from odys.optimization.model.milp_model import EnergyMILPModel


class CVaRConstraints(ConstraintGroup):
    """Builds the shortfall constraint for CVaR: z_s >= η - profit_s for all scenarios."""

    def __init__(self, milp_model: EnergyMILPModel) -> None:
        """Initialize with the MILP model containing CVaR variables."""
        self.model = milp_model

    @constraint
    def _get_shortfall_constraint(self) -> ModelConstraint:
        constraint_expr = (
            self.model.vars.shortfall_revenue >= self.model.vars.value_at_risk - self.model.per_scenario_profit()
        )
        return ModelConstraint(
            constraint=constraint_expr,
            name="cvar_shortfall_constraint",
        )
