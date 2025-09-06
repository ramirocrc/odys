import linopy

from optimes._math_model.model_components.constraints.model_constraint import ModelConstraint
from optimes._math_model.model_components.parameters import GeneratorParameters
from optimes._math_model.model_components.variables import ModelVariable


class GeneratorConstraints:
    def __init__(self, linopy_model: linopy.Model, params: GeneratorParameters) -> None:
        self.model = linopy_model
        self.params = params
        self.var_generator_power = self.model.variables[ModelVariable.GENERATOR_POWER.var_name]

    @property
    def all(self) -> tuple[ModelConstraint, ...]:
        return (self.get_generator_max_power_constraint(),)

    def get_generator_max_power_constraint(self) -> ModelConstraint:
        """Generator power limit constraint.

        This constraint ensures that each generator's power output does not
        exceed its nominal power capacity.
        """
        constraint = self.var_generator_power <= self.params.generators_nominal_power
        return ModelConstraint(
            constraint=constraint,
            name="generator_max_power_constraint",
        )
