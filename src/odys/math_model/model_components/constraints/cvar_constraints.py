"""CVaR (Conditional Value at Risk) constraints for stochastic optimization."""

from odys.math_model.milp_model import EnergyMILPModel
from odys.math_model.model_components.constraints.constraints_group import ConstraintGroup, constraint
from odys.math_model.model_components.constraints.model_constraint import ModelConstraint


class CVaRConstraints(ConstraintGroup):
    """Builds the shortfall constraint for CVaR: z_s >= η - profit_s for all scenarios."""

    def __init__(self, milp_model: EnergyMILPModel) -> None:
        """Initialize with the MILP model containing CVaR variables."""
        self.model = milp_model

    @constraint
    def _get_shortfall_constraint(self) -> ModelConstraint:
        constraint_expr = self.model.cvar_shortfall >= self.model.cvar_value_at_risk - self.model.per_scenario_profit()
        return ModelConstraint(
            constraint=constraint_expr,
            name="cvar_shortfall_constraint",
        )
