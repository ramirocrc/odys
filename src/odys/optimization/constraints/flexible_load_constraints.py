"""Flexible load constraints for the optimization model."""

from odys.optimization.constraints.constraints_group import ConstraintGroup, constraint
from odys.optimization.constraints.model_constraint import ModelConstraint
from odys.optimization.model.milp_model import EnergyMILPModel


class FlexibleLoadConstraints(ConstraintGroup):
    """Builds constraints for flexible load adjustment bounds."""

    def __init__(self, milp_model: EnergyMILPModel) -> None:
        """Initialize with the MILP model and flexible load parameters."""
        self.model = milp_model
        self.params = milp_model.parameters.flexible_loads

    @constraint
    def _get_adjustment_lower_bound_constraint(self) -> ModelConstraint:
        """Flexible load adjustment lower bound constraint.

        This constraint ensures that each flexible load's adjustment is not less than
        -max_decrease (i.e., cannot decrease more than max_decrease).
        """
        return ModelConstraint(
            constraint=self.model.load_adjustment >= -self.params.max_decrease,
            name="flexible_load_adjustment_lower_bound_constraint",
        )

    @constraint
    def _get_adjustment_upper_bound_constraint(self) -> ModelConstraint:
        """Flexible load adjustment upper bound constraint.

        This constraint ensures that each flexible load's adjustment is not greater than
        max_increase (i.e., cannot increase more than max_increase).
        """
        return ModelConstraint(
            constraint=self.model.load_adjustment <= self.params.max_increase,
            name="flexible_load_adjustment_upper_bound_constraint",
        )
