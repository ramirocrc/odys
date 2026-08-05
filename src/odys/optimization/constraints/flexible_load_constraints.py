"""Flexible load constraints for the optimization model."""

from __future__ import annotations

from typing import TYPE_CHECKING

from odys.optimization.constraints.constraints_group import ConstraintGroup, constraint
from odys.optimization.constraints.model_constraint import ModelConstraint

if TYPE_CHECKING:
    from odys.optimization.model.milp_model import EnergyMILPModel
    from odys.parameters.entity_parameters.flexible_load_parameters import FlexibleLoadParameters


class FlexibleLoadConstraints(ConstraintGroup):
    """Builds constraints for flexible load adjustment bounds."""

    def __init__(self, milp_model: EnergyMILPModel) -> None:
        """Initialize with the MILP model and flexible load parameters."""
        self.model = milp_model
        flex = milp_model.parameters.flexible_loads
        if flex is None:
            msg = "FlexibleLoadConstraints requires flexible loads to be present."
            raise ValueError(msg)
        self.params: FlexibleLoadParameters = flex

    @constraint
    def _get_adjustment_lower_bound_constraint(self) -> ModelConstraint:
        """Flexible load adjustment lower bound constraint.

        This constraint ensures that each flexible load's adjustment is not less than
        -max_decrease (i.e., cannot decrease more than max_decrease).
        """
        return ModelConstraint(
            constraint=self.model.vars.load_adjustment >= -self.params.max_decrease,
            name="flexible_load_adjustment_lower_bound_constraint",
        )

    @constraint
    def _get_adjustment_upper_bound_constraint(self) -> ModelConstraint:
        """Flexible load adjustment upper bound constraint.

        This constraint ensures that each flexible load's adjustment is not greater than
        max_increase (i.e., cannot increase more than max_increase).
        """
        return ModelConstraint(
            constraint=self.model.vars.load_adjustment <= self.params.max_increase,
            name="flexible_load_adjustment_upper_bound_constraint",
        )
