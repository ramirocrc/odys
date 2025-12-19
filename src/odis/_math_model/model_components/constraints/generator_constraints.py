from odis._math_model.milp_model import EnergyMILPModel
from odis._math_model.model_components.constraints.model_constraint import ModelConstraint


class GeneratorConstraints:
    def __init__(self, milp_model: EnergyMILPModel) -> None:
        self.model = milp_model
        self.params = milp_model.parameters.generators

    def _validate_generator_parameters_exist(self) -> None:
        if self.params is None:
            msg = "No generator parameters specified."
            raise ValueError(msg)

    @property
    def all(self) -> tuple[ModelConstraint, ...]:
        if self.params is None:
            return ()
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
        self._validate_generator_parameters_exist()
        constraint = self.model.generator_power - self.model.generator_status * self.params.nominal_power <= 0  # ty: ignore # pyrefly: ignore
        return ModelConstraint(
            constraint=constraint,
            name="generator_max_power_constraint",
        )

    def _get_generator_status_constraint(self) -> ModelConstraint:
        self._validate_generator_parameters_exist()
        epsilon = 1e-5 * self.params.nominal_power  # ty: ignore # pyrefly: ignore
        constraint = self.model.generator_power >= self.model.generator_status * epsilon  # ty: ignore # pyrefly: ignore
        return ModelConstraint(
            constraint=constraint,
            name="generator_status_constraint",
        )

    def _get_generator_startup_lower_bound_constraint(self) -> ModelConstraint:
        constraint = self.model.generator_startup >= self.model.generator_status - self.model.generator_status.shift(
            time=1,
        )
        return ModelConstraint(
            constraint=constraint,
            name="generator_startup_lower_bound_constraint",
        )

    def _get_generator_startup_upper_bound_1_constraint(self) -> ModelConstraint:
        return ModelConstraint(
            constraint=self.model.generator_startup <= self.model.generator_status,
            name="generator_startup_upper_bound_1_constraint",
        )

    def _get_generator_startup_upper_bound_2_constraint(self) -> ModelConstraint:
        return ModelConstraint(
            constraint=self.model.generator_startup + self.model.generator_status.shift(time=1) <= 1.0,
            name="generator_startup_upper_bound_2_constraint",
        )

    def _get_generator_shutdown_lower_bound_constraint(self) -> ModelConstraint:
        constraint = (
            self.model.generator_shutdown >= self.model.generator_status.shift(time=1) - self.model.generator_status
        )
        return ModelConstraint(
            constraint=constraint,
            name="generator_shutdown_lower_bound_constraint",
        )

    def _get_generator_shutdown_upper_bound_1_constraint(self) -> ModelConstraint:
        return ModelConstraint(
            constraint=self.model.generator_shutdown <= self.model.generator_status.shift(time=1),
            name="generator_shutdown_upper_bound_1_constraint",
        )

    def _get_generator_shutdown_upper_bound_2_constraint(self) -> ModelConstraint:
        return ModelConstraint(
            constraint=self.model.generator_shutdown + self.model.generator_status <= 1.0,
            name="generator_shutdown_upper_bound_2_constraint",
        )

    def _get_min_uptime_constraint(self) -> list[ModelConstraint]:
        self._validate_generator_parameters_exist()
        constraints = []
        for generator in self.params.index.values:  # ty: ignore # pyrefly: ignore
            min_up_time = int(self.params.min_up_time.sel(generator=generator))  # ty: ignore # pyrefly: ignore
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

    def _get_min_power_constraint(self) -> ModelConstraint:
        self._validate_generator_parameters_exist()
        return ModelConstraint(
            constraint=self.model.generator_power >= self.params.min_power * self.model.generator_status,  # ty: ignore # pyrefly: ignore
            name="generator_min_power_constraint",
        )

    def _get_max_ramp_up_constraint(self) -> ModelConstraint:
        self._validate_generator_parameters_exist()
        max_ramp_up = self.params.max_ramp_up.fillna(self.params.nominal_power)  # ty: ignore # pyrefly: ignore
        return ModelConstraint(
            constraint=self.model.generator_power - self.model.generator_power.shift(time=1) <= max_ramp_up,
            name="generator_max_ramp_up_constraint",
        )

    def _get_max_ramp_down_constraint(self) -> ModelConstraint:
        self._validate_generator_parameters_exist()
        max_ramp_down = self.params.max_ramp_down.fillna(self.params.nominal_power)  # ty: ignore # pyrefly: ignore
        constraint = self.model.generator_power.shift(time=1) - self.model.generator_power <= max_ramp_down

        return ModelConstraint(
            constraint=constraint,
            name="generator_max_ramp_down_constraint",
        )
