import linopy

from optimes._math_model.model_components.constraints.model_constraint import ModelConstraint
from optimes._math_model.model_components.parameters import GeneratorParameters
from optimes._math_model.model_components.variables import ModelVariable


class GeneratorConstraints:
    def __init__(self, linopy_model: linopy.Model, params: GeneratorParameters) -> None:
        self.model = linopy_model
        self.params = params
        self.var_generator_power = self.model.variables[ModelVariable.GENERATOR_POWER.var_name]
        self.var_generator_status = self.model.variables[ModelVariable.GENERATOR_STATUS.var_name]
        self.var_generator_startup = self.model.variables[ModelVariable.GENERATOR_STARTUP.var_name]
        self.var_generator_shutdown = self.model.variables[ModelVariable.GENERATOR_SHUTDOWN.var_name]

    @property
    def all(self) -> tuple[ModelConstraint, ...]:
        return (
            self._get_generator_max_power_constraint(),
            self._get_generator_status_constraint(),
            self._get_generator_startup_lower_bound_constraint(),
            self._get_generator_startup_upper_bound_1_constraint(),
            self._get_generator_startup_upper_bound_2_constraint(),
            self._get_generator_shutdown_lower_bound_constraint(),
            self._get_generator_shutdown_upper_bound_1_constraint(),
            self._get_generator_shutdown_upper_bound_2_constraint(),
            *self._get_min_uptime_constraint(),
            self._get_min_power_constraint(),
            self._get_max_ramp_up_constraint(),
            self._get_max_ramp_down_constraint(),
        )

    def _get_generator_max_power_constraint(self) -> ModelConstraint:
        """Generator power limit constraint.

        This constraint ensures that each generator's power output does not
        exceed its nominal power capacity.
        """
        constraint = self.var_generator_power - self.var_generator_status * self.params.nominal_power <= 0  # pyright: ignore reportOperatorIssue
        return ModelConstraint(
            constraint=constraint,
            name="generator_max_power_constraint",
        )

    def _get_generator_status_constraint(self) -> ModelConstraint:
        epsilon = 1e-5 * self.params.nominal_power
        constraint = self.var_generator_power >= self.var_generator_status * epsilon  # pyright: ignore reportOperatorIssue
        return ModelConstraint(
            constraint=constraint,
            name="generator_status_constraint",
        )

    def _get_generator_startup_lower_bound_constraint(self) -> ModelConstraint:
        constraint = self.var_generator_startup >= self.var_generator_status - self.var_generator_status.shift(time=1)
        return ModelConstraint(
            constraint=constraint,
            name="generator_startup_lower_bound_constraint",
        )

    def _get_generator_startup_upper_bound_1_constraint(self) -> ModelConstraint:
        return ModelConstraint(
            constraint=self.var_generator_startup <= self.var_generator_status,
            name="generator_startup_upper_bound_1_constraint",
        )

    def _get_generator_startup_upper_bound_2_constraint(self) -> ModelConstraint:
        return ModelConstraint(
            constraint=self.var_generator_startup + self.var_generator_status.shift(time=1) <= 1.0,
            name="generator_startup_upper_bound_2_constraint",
        )

    def _get_generator_shutdown_lower_bound_constraint(self) -> ModelConstraint:
        constraint = self.var_generator_shutdown >= self.var_generator_status.shift(time=1) - self.var_generator_status
        return ModelConstraint(
            constraint=constraint,
            name="generator_shutdown_lower_bound_constraint",
        )

    def _get_generator_shutdown_upper_bound_1_constraint(self) -> ModelConstraint:
        return ModelConstraint(
            constraint=self.var_generator_shutdown <= self.var_generator_status.shift(time=1),
            name="generator_shutdown_upper_bound_1_constraint",
        )

    def _get_generator_shutdown_upper_bound_2_constraint(self) -> ModelConstraint:
        return ModelConstraint(
            constraint=self.var_generator_shutdown + self.var_generator_status <= 1.0,
            name="generator_shutdown_upper_bound_2_constraint",
        )

    def _get_min_uptime_constraint(self) -> tuple[ModelConstraint, ...]:
        constraints = []
        for generator in self.params.set.values:
            min_up_time = int(self.params.min_up_time.sel(generators=generator).values)
            generator_status = self.var_generator_status.sel(generators=generator)
            generator_shutdown = self.var_generator_shutdown.sel(generators=generator)
            constraint_generator = generator_status.rolling(
                time=min_up_time,
            ).sum() >= min_up_time * generator_shutdown.shift(time=-1)
            constraints.append(
                ModelConstraint(
                    constraint=constraint_generator,
                    name=f"generator_min_uptime_{generator}_constraint",
                ),
            )

        return tuple(constraints)

    def _get_min_power_constraint(self) -> ModelConstraint:
        return ModelConstraint(
            constraint=self.var_generator_power >= self.params.min_power * self.var_generator_status,
            name="generator_min_power_constraint",
        )

    def _get_max_ramp_up_constraint(self) -> ModelConstraint:
        return ModelConstraint(
            constraint=self.var_generator_power - self.var_generator_power.shift(time=1) <= self.params.max_ramp_up,
            name="generator_max_ramp_up_constraint",
        )

    def _get_max_ramp_down_constraint(self) -> ModelConstraint:
        constraint = self.var_generator_power.shift(time=1) - self.var_generator_power <= self.params.max_ramp_down

        return ModelConstraint(
            constraint=constraint,
            name="generator_max_ramp_down_constraint",
        )
