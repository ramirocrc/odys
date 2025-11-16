from collections.abc import Iterable
from functools import cached_property

from optimes._math_model.milp_model import EnergyMILPModel
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
    get_variable_lower_bound,
)
from optimes._math_model.model_components.objectives import (
    ObjectiveFuncions,
)
from optimes._math_model.model_components.parameters.parameters import EnergySystemParameters
from optimes._math_model.model_components.sets import ModelDimension, ModelIndex
from optimes._math_model.model_components.variables import (
    BATTERY_VARIABLES,
    GENERATOR_VARIABLES,
    MARKET_VARIABLES,
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
        energy_system_parameters: EnergySystemParameters,
        *,
        enforce_non_anticipativity: bool,
    ) -> None:
        """Initialize the model builder with validated energy system.

        Args:
            energy_system_parameters:  Paramteres of the energy system,
                containing all assets, demand profiles, and constraints.
            enforce_non_anticipativity: When True, decision variables must take the same values across all scenarios,
        """
        self._milp_model = EnergyMILPModel(energy_system_parameters)
        self.enforce_non_anticipativity = enforce_non_anticipativity
        self._model_is_built: bool = False

    def build(self) -> EnergyMILPModel:
        if self._model_is_built:
            msg = "Model has already been built."
            raise AttributeError(msg)
        self._add_model_variables()
        self._add_model_constraints()
        self._add_model_objective()
        self._model_is_built = True

        return self._milp_model

    def _add_model_variables(self) -> None:
        variables_to_add = []
        if self._milp_model.parameters.generators:
            variables_to_add.extend(GENERATOR_VARIABLES)

        if self._milp_model.parameters.batteries:
            variables_to_add.extend(BATTERY_VARIABLES)

        if self._milp_model.parameters.markets:
            variables_to_add.extend(MARKET_VARIABLES)

        for variable in variables_to_add:
            linopy_variable = self._get_linopy_variable_params(variable)
            self.add_variable_to_model(linopy_variable)

    def _get_linopy_variable_params(self, variable: ModelVariable) -> LinopyVariableParameters:
        coordinates = {}
        dimensions = []
        indeces = []

        for dimension in variable.dimensions:
            index = self.get_index_for_dimension(dimension)
            coordinates |= index.coordinates
            dimensions.append(index.dimension)
            indeces.append(index)

        return LinopyVariableParameters(
            name=variable.var_name,
            coords=coordinates,
            dims=dimensions,
            lower=get_variable_lower_bound(
                indeces=indeces,
                lower_bound_type=variable.lower_bound_type,
                is_binary=variable.is_binary,
            ),
            binary=variable.is_binary,
        )

    def get_index_for_dimension(self, dimension: ModelDimension) -> ModelIndex:
        index = self._dimension_to_index_mapping.get(dimension)
        if index is None:
            msg = f"No index found for dimension '{dimension}'."
            raise ValueError(msg)
        return index

    @cached_property
    def _dimension_to_index_mapping(self) -> dict[ModelDimension, ModelIndex | None]:
        return {
            ModelDimension.Scenarios: self._milp_model.indices.scenarios,
            ModelDimension.Time: self._milp_model.indices.time,
            ModelDimension.Generators: self._milp_model.indices.generators,
            ModelDimension.Batteries: self._milp_model.indices.batteries,
            ModelDimension.Loads: self._milp_model.indices.loads,
            ModelDimension.Markets: self._milp_model.indices.markets,
        }

    def add_variable_to_model(self, variable: LinopyVariableParameters) -> None:
        self._milp_model.linopy_model.add_variables(
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
        constraints = BatteryConstraints(milp_model=self._milp_model).all
        self._add_set_of_contraints_to_model(constraints)

    def _add_generator_constraints(self) -> None:
        constraints = GeneratorConstraints(self._milp_model).all
        self._add_set_of_contraints_to_model(constraints)

    def _add_scenario_constraints(self) -> None:
        constraints = ScenarioConstraints(
            milp_model=self._milp_model,
            enforce_non_anticipativity=self.enforce_non_anticipativity,
        ).all
        self._add_set_of_contraints_to_model(constraints)

    def _add_set_of_contraints_to_model(self, constraints: Iterable[ModelConstraint]) -> None:
        for constraint in constraints:
            self._milp_model.linopy_model.add_constraints(
                constraint.constraint,
                name=constraint.name,
            )

    def _add_model_objective(self) -> None:
        objective = ObjectiveFuncions(milp_model=self._milp_model).profit
        self._milp_model.linopy_model.add_objective(objective, sense="max")
