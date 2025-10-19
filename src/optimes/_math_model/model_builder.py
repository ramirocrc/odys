from collections.abc import Iterable
from functools import cached_property

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
    get_variable_lower_bound,
)
from optimes._math_model.model_components.objectives import (
    ObjectiveFuncions,
)
from optimes._math_model.model_components.parameters import EnergyModelParameters
from optimes._math_model.model_components.sets import ModelDimension, ModelIndex
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
        for variable in ModelVariable:
            linopy_variable = self._get_linopy_variable_params(variable)
            # todo: If variable coordinates has a zero in one dimension it means that it's not needed and can be skipped
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
        if not index:
            msg = f"No index found for dimension {dimension}."
            raise ValueError(msg)
        return index

    @cached_property
    def _dimension_to_index_mapping(self) -> dict[ModelDimension, ModelIndex]:
        return {
            ModelDimension.Scenarios: self._parameters.system.scenario_index,
            ModelDimension.Time: self._parameters.system.time_index,
            ModelDimension.Generators: self._parameters.generators.index,
            ModelDimension.Batteries: self._parameters.batteries.index,
            ModelDimension.Loads: self._parameters.loads.index,
            ModelDimension.Markets: self._parameters.markets.index,
        }

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
        objective = ObjectiveFuncions(
            var_generator_power=self._linopy_model.variables[ModelVariable.GENERATOR_POWER.var_name],
            var_generator_startup=self._linopy_model.variables[ModelVariable.GENERATOR_STARTUP.var_name],
            var_market_traded_vol=self._linopy_model.variables[ModelVariable.MARKET_TRADED_VOLUME.var_name],
            param_generator_variable_cost=self._parameters.generators.variable_cost,
            param_generator_startup_cost=self._parameters.generators.startup_cost,
            param_scenario_probabilities=self._parameters.system.scenario_probabilities,
            param_market_prices=self._parameters.system.market_prices,
        ).profit
        self._linopy_model.add_objective(objective, sense="max")
