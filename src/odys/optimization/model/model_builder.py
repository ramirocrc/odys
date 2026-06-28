"""Builder for constructing linopy optimization models from energy system parameters.

This module provides the EnergyAlgebraicModelBuilder that assembles
variables, constraints, and objectives into a solvable MILP model.
"""

from odys.domain.exceptions import OdysError
from odys.optimization.constraints.constraints_group import ConstraintGroup
from odys.optimization.constraints.cvar_constraints import CVaRConstraints
from odys.optimization.constraints.generator_constraints import (
    GeneratorConstraints,
)
from odys.optimization.constraints.market_constraints import MarketConstraints
from odys.optimization.constraints.scenario_constraints import (
    ScenarioConstraints,
)
from odys.optimization.constraints.storage_constraints import (
    StorageConstraints,
)
from odys.optimization.model.linopy_converter import (
    LinopyVariableParameters,
    get_variable_lower_bound,
)
from odys.optimization.model.milp_model import EnergyMILPModel
from odys.optimization.model.objectives import build_objective
from odys.optimization.model.registry import AssetRegistry
from odys.optimization.model.variables import (
    CVAR_VARIABLES,
    ModelVariable,
)
from odys.optimization.parameters.parameters import EnergySystemParameters


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
    ) -> None:
        """Initialize the model builder with validated energy system.

        Args:
            energy_system_parameters: Parameters of the energy system,
                containing all assets, demand profiles, and constraints.
        """
        self._milp_model = EnergyMILPModel(energy_system_parameters)
        self._model_is_built: bool = False

    def build(self) -> EnergyMILPModel:
        """Build the complete optimization model with variables, constraints, and objective.

        Returns:
            The fully constructed EnergyMILPModel ready for solving.

        Raises:
            OdysError: If the model has already been built.

        """
        if self._model_is_built:
            msg = "Model has already been built."
            raise OdysError(msg)
        self._add_model_variables()
        self._add_model_constraints()
        self._add_model_objective()
        self._model_is_built = True

        return self._milp_model

    def _add_model_variables(self) -> None:
        params = self._milp_model.parameters
        variables_to_add: list[ModelVariable] = []

        for asset in AssetRegistry:
            param = getattr(params, asset.name.lower() + "s")
            if not param.is_empty:
                variables_to_add.extend(asset.spec.variables)

        if params.objective.cvar is not None:
            variables_to_add.extend(CVAR_VARIABLES)

        for variable in variables_to_add:
            linopy_variable = self._get_linopy_variable_params(variable)
            self.add_variable_to_model(linopy_variable)

    def _get_linopy_variable_params(self, variable: ModelVariable) -> LinopyVariableParameters:
        coordinates = {}
        dimensions = []
        indices = []

        if variable.dimensions is not None:
            for dimension in variable.dimensions:
                index = self._milp_model.indices.get_index(dimension)
                coordinates |= index.coordinates
                dimensions.append(index.dimension)
                indices.append(index)

        return LinopyVariableParameters(
            name=variable.var_name,
            coords=coordinates,
            dims=dimensions,
            lower=get_variable_lower_bound(
                indeces=indices,
                lower_bound_type=variable.lower_bound_type,
                is_binary=variable.is_binary,
            ),
            binary=variable.is_binary,
        )

    def add_variable_to_model(self, variable: LinopyVariableParameters) -> None:
        """Add a variable to the underlying linopy model.

        Args:
            variable: Variable parameters to add to the linopy model.
        """
        self._milp_model.linopy_model.add_variables(
            name=variable.name,
            coords=variable.coords,
            dims=variable.dims,
            lower=variable.lower,
            binary=variable.binary,
        )

    def _add_model_constraints(self) -> None:
        for group in self._get_constraint_groups():
            group.add_to_model(self._milp_model.linopy_model)

    def _get_constraint_groups(self) -> list[ConstraintGroup]:
        groups: list[ConstraintGroup] = []
        params = self._milp_model.parameters

        if params.has_generators:
            groups.append(GeneratorConstraints(self._milp_model))

        if params.has_storages:
            groups.append(StorageConstraints(self._milp_model))

        if params.has_markets:
            groups.append(MarketConstraints(self._milp_model))

        groups.append(ScenarioConstraints(self._milp_model))

        if params.objective.cvar is not None:
            groups.append(CVaRConstraints(self._milp_model))

        return groups

    def _add_model_objective(self) -> None:
        objective = build_objective(self._milp_model, self._milp_model.parameters.objective)
        self._milp_model.linopy_model.add_objective(objective, sense="max")


def build_model(energy_system_parameters: EnergySystemParameters) -> EnergyMILPModel:
    """Build an optimization model from energy system parameters.

    Args:
        energy_system_parameters: Validated energy system parameters.

    Returns:
        EnergyMILPModel ready for solving.

    """
    builder = EnergyAlgebraicModelBuilder(energy_system_parameters)
    return builder.build()
