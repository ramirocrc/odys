"""Generator-related constraints for the optimization model."""

from odys.math_model.milp_model import EnergyMILPModel
from odys.math_model.model_components.constraints.constraints_group import ConstraintGroup, constraint
from odys.math_model.model_components.constraints.model_constraint import ModelConstraint
from odys.math_model.model_components.parameters.generator_parameters import GeneratorParameters


class GeneratorConstraints(ConstraintGroup):
    """Builds constraints for generator power limits, ramping, startup/shutdown, and min uptime."""

    def __init__(self, milp_model: EnergyMILPModel, params: GeneratorParameters) -> None:
        """Initialize with the MILP model and generator parameters."""
        self.model = milp_model
        self.params = params

    @constraint
    def _get_generator_max_power_constraint(self) -> ModelConstraint:
        """Generator power limit constraint.

        This constraint ensures that each generator's power output does not
        exceed its nominal power capacity.
        """
        return ModelConstraint(
            constraint=self.model.generator_power - self.model.generator_status * self.params.nominal_power <= 0,
            name="generator_max_power_constraint",
        )

    @constraint
    def _get_generator_status_constraint(self) -> ModelConstraint:
        epsilon = 1e-5 * self.params.nominal_power
        return ModelConstraint(
            constraint=self.model.generator_power >= self.model.generator_status * epsilon,
            name="generator_status_constraint",
        )

    @constraint
    def _get_generator_startup_lower_bound_constraint(self) -> ModelConstraint:
        return ModelConstraint(
            constraint=self.model.generator_startup
            >= self.model.generator_status
            - self.model.generator_status.shift(
                time=1,
            ),
            name="generator_startup_lower_bound_constraint",
        )

    @constraint
    def _get_generator_startup_upper_bound_1_constraint(self) -> ModelConstraint:
        return ModelConstraint(
            constraint=self.model.generator_startup <= self.model.generator_status,
            name="generator_startup_upper_bound_1_constraint",
        )

    @constraint
    def _get_generator_startup_upper_bound_2_constraint(self) -> ModelConstraint:
        return ModelConstraint(
            constraint=self.model.generator_startup + self.model.generator_status.shift(time=1) <= 1.0,
            name="generator_startup_upper_bound_2_constraint",
        )

    @constraint
    def _get_generator_shutdown_lower_bound_constraint(self) -> ModelConstraint:
        return ModelConstraint(
            constraint=self.model.generator_shutdown
            >= self.model.generator_status.shift(time=1) - self.model.generator_status,
            name="generator_shutdown_lower_bound_constraint",
        )

    @constraint
    def _get_generator_shutdown_upper_bound_1_constraint(self) -> ModelConstraint:
        return ModelConstraint(
            constraint=self.model.generator_shutdown <= self.model.generator_status.shift(time=1),
            name="generator_shutdown_upper_bound_1_constraint",
        )

    @constraint
    def _get_generator_shutdown_upper_bound_2_constraint(self) -> ModelConstraint:
        return ModelConstraint(
            constraint=self.model.generator_shutdown + self.model.generator_status <= 1.0,
            name="generator_shutdown_upper_bound_2_constraint",
        )

    @constraint
    def _get_min_uptime_constraint(self) -> list[ModelConstraint]:
        constraints = []
        for generator in self.params.index.values:
            min_up_time = int(self.params.min_up_time.sel(generator=generator))
            generator_status = self.model.generator_status.sel(generator=generator)
            generator_shutdown = self.model.generator_shutdown.sel(generator=generator)
            constraint_generator = generator_status.rolling(
                time=min_up_time,
            ).sum() >= min_up_time * generator_shutdown.shift(time=-1)
            constraints.append(
                ModelConstraint(
                    constraint=constraint_generator,
                    name=f"generator_min_uptime_{generator}_constraint",
                ),
            )
        return constraints

    @constraint
    def _get_min_power_constraint(self) -> ModelConstraint:
        return ModelConstraint(
            constraint=self.model.generator_power >= self.params.min_power * self.model.generator_status,
            name="generator_min_power_constraint",
        )

    @constraint
    def _get_max_ramp_up_constraint(self) -> ModelConstraint:
        max_ramp_up = self.params.max_ramp_up.fillna(self.params.nominal_power)
        constraint_expr = self.model.generator_power - self.model.generator_power.shift(time=1) <= max_ramp_up
        return ModelConstraint(
            constraint=constraint_expr.isel(time=slice(1, None)),
            name="generator_max_ramp_up_constraint",
        )

    @constraint
    def _get_max_ramp_down_constraint(self) -> ModelConstraint:
        max_ramp_down = self.params.max_ramp_down.fillna(self.params.nominal_power)
        constraint_expr = self.model.generator_power.shift(time=1) - self.model.generator_power <= max_ramp_down
        return ModelConstraint(
            constraint=constraint_expr.isel(time=slice(1, None)),
            name="generator_max_ramp_down_constraint",
        )
