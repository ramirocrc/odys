from collections.abc import Iterable

from linopy import Model

from optimes._math_model.model_components.constraints.battery_constraints import (
    BatteryConstraints,
)
from optimes._math_model.model_components.constraints.generator_constraints import (
    GeneratorConstraints,
)
from optimes._math_model.model_components.constraints.model_constraint import ModelConstraint
from optimes._math_model.model_components.constraints.scenario_constraints import (
    ScenarioConstraints,
)
from optimes._math_model.model_components.linopy_converter import (
    LinopyVariableParameters,
    get_linopy_variable_parameters,
)
from optimes._math_model.model_components.objectives import (
    get_operating_costs,
)
from optimes._math_model.model_components.parameters import EnergyModelParameters
from optimes._math_model.model_components.variables import (
    ModelVariable,
)
from optimes.utils.logging import get_logger

logger = get_logger(__name__)


class EnergyAlgebraicModelBuilder:
    """Builder class for constructing algebraic energy system optimization models.

    This class takes a validated energy system configuration and builds
    a complete linopy optimization model including variables, constraints,
    and objectives ready for solving.

    The builder ensures the model is constructed only once and prevents
    multiple builds of the same instance.
    """

    def __init__(
        self,
        energy_system_parameters: EnergyModelParameters,
    ) -> None:
        """Initialize the model builder with validated energy system.

        Args:
            energy_system_parameters:  Paramteres of the energy system,
                containing all assets, demand profiles, and constraints.
        """
        self._parameters = energy_system_parameters
        self._linopy_model = Model(force_dim_names=True)
        self._model_is_built: bool = False

    def build(self) -> Model:
        if self._model_is_built:
            msg = "Model has already been built."
            raise AttributeError(msg)
        self._add_model_variables()
        self._add_model_constraints()
        self._add_model_objective()
        self._model_is_built = True

        return self._linopy_model

    def _add_model_variables(self) -> None:
        for generator_variable_i in ModelVariable.generator_variables():
            linopy_variable_parameters = get_linopy_variable_parameters(
                variable=generator_variable_i,
                time_set=self._parameters.system.time_set,
                asset_set=self._parameters.generators.set,
            )
            self.add_variable_to_model(linopy_variable_parameters)

        for battery_variable_i in ModelVariable.battery_variables():
            linopy_variable_parameters = get_linopy_variable_parameters(
                variable=battery_variable_i,
                time_set=self._parameters.system.time_set,
                asset_set=self._parameters.batteries.set,
            )
            self.add_variable_to_model(linopy_variable_parameters)

    def add_variable_to_model(self, variable: LinopyVariableParameters) -> None:
        self._linopy_model.add_variables(
            name=variable.name,
            coords=variable.coords,
            dims=variable.dims,
            lower=variable.lower,
            binary=variable.binary,
        )

    def _add_model_constraints(self) -> None:
        self._add_generator_constraints()
        self._add_battery_constraints()
        self._add_scenario_constraints()

    def _add_battery_constraints(self) -> None:
        constraints = BatteryConstraints(
            linopy_model=self._linopy_model,
            params=self._parameters.batteries,
        ).all
        self._add_set_of_contraints_to_model(constraints)

    def _add_generator_constraints(self) -> None:
        constraints = GeneratorConstraints(
            self._linopy_model,
            self._parameters.generators,
        ).all
        self._add_set_of_contraints_to_model(constraints)

    def _add_scenario_constraints(self) -> None:
        constraints = ScenarioConstraints(
            linopy_model=self._linopy_model,
            params=self._parameters.system,
        ).all
        self._add_set_of_contraints_to_model(constraints)

    def _add_set_of_contraints_to_model(self, constraints: Iterable[ModelConstraint]) -> None:
        for constraint in constraints:
            self._linopy_model.add_constraints(
                constraint.constraint,
                name=constraint.name,
            )

    def _add_model_objective(self) -> None:
        objective = get_operating_costs(
            var_generator_power=self._linopy_model.variables[ModelVariable.GENERATOR_POWER.var_name],
            var_generator_startup=self._linopy_model.variables[ModelVariable.GENERATOR_STARTUP.var_name],
            param_generator_variable_cost=self._parameters.generators.variable_cost,
            param_generator_startup_cost=self._parameters.generators.startup_cost,
        )
        self._linopy_model.add_objective(objective)
