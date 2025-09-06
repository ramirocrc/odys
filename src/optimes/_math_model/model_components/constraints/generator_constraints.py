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

    @property
    def all(self) -> tuple[ModelConstraint, ...]:
        return (
            self._get_generator_max_power_constraint(),
            self._get_generator_status_constraint(),
        )

    def _get_generator_max_power_constraint(self) -> ModelConstraint:
        """Generator power limit constraint.

        This constraint ensures that each generator's power output does not
        exceed its nominal power capacity.
        """
        constraint = self.var_generator_power - self.var_generator_status * self.params.generators_nominal_power <= 0  # pyright: ignore reportOperatorIssue
        return ModelConstraint(
            constraint=constraint,
            name="generator_max_power_constraint",
        )

    def _get_generator_status_constraint(self) -> ModelConstraint:
        epsilon = 1e-5 * self.params.generators_nominal_power
        constraint = self.var_generator_power >= self.var_generator_status * epsilon  # pyright: ignore reportOperatorIssue
        return ModelConstraint(
            constraint=constraint,
            name="generator_status_constraint",
        )
