"""Charger-related constraints for the optimization model."""

from odys.optimization.constraints.constraints_group import ConstraintGroup, constraint
from odys.optimization.constraints.model_constraint import ModelConstraint
from odys.optimization.model.milp_model import EnergyMILPModel
from odys.optimization.model.sets import ModelDimension


class ChargerConstraints(ConstraintGroup):
    """Builds constraints for charger assignment and power limits.

    These constraints only apply to ElectricVehicle instances.
    StandaloneStorage assets are not affected by charger constraints.
    """

    def __init__(self, milp_model: EnergyMILPModel) -> None:
        """Initialize with the MILP model and charger parameters."""
        self.model = milp_model
        self.charger_params = milp_model.parameters.chargers
        self.ev_params = milp_model.parameters.electric_vehicles

    @constraint
    def _get_charger_one_ev_per_charger_constraint(self) -> ModelConstraint:
        """Each charger can serve at most one EV at a time."""
        assignment = self.model.vars.charger_ev_assignment
        return ModelConstraint(
            constraint=assignment.sum(ModelDimension.EVs.value) <= 1,
            name="charger_one_ev_per_charger_constraint",
        )

    @constraint
    def _get_charger_one_charger_per_ev_constraint(self) -> ModelConstraint:
        """Each EV can be connected to at most one charger at a time."""
        assignment = self.model.vars.charger_ev_assignment
        return ModelConstraint(
            constraint=assignment.sum(ModelDimension.Chargers.value) <= 1,
            name="charger_one_charger_per_ev_constraint",
        )

    @constraint
    def _get_charger_no_assignment_while_driving_constraint(self) -> ModelConstraint:
        """EVs cannot be assigned to a charger while driving."""
        assignment = self.model.vars.charger_ev_assignment
        is_driving = self.ev_params.is_driving

        return ModelConstraint(
            constraint=assignment <= 1 - is_driving,
            name="charger_no_assignment_while_driving_constraint",
        )

    @constraint
    def _get_charger_power_limit_constraint(self) -> ModelConstraint:
        """EV charging and discharging power limited by the assigned charger's max_power.

        With no charger assigned the right-hand side is 0; an EV must be
        assigned to a charger to charge or discharge (V2G included).
        """
        assignment = self.model.vars.charger_ev_assignment
        available_power = (assignment * self.charger_params.max_power).sum(ModelDimension.Chargers.value)

        power_in = self.model.vars.ev_power_in
        power_out = self.model.vars.ev_power_out

        return ModelConstraint(
            constraint=power_in + power_out <= available_power,
            name="charger_power_limit_constraint",
        )
