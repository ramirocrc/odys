"""Builder for constructing linopy optimization models from energy system parameters.

This module provides the EnergyAlgebraicModelBuilder that assembles
variables, constraints, and objectives into a solvable MILP model.
"""

from odys.domain.exceptions import OdysError
from odys.domain.objective import CVaRTerm
from odys.optimization.constraints.constraints_group import ConstraintGroup
from odys.optimization.constraints.cvar_constraints import CVaRConstraints
from odys.optimization.model.linopy_converter import get_linopy_variable_parameters
from odys.optimization.model.milp_model import EnergyMILPModel
from odys.optimization.model.objectives import build_objective
from odys.optimization.model.variable_definitions import (
    CVAR_VARIABLES,
    VariableDefinitionRegistry,
)
from odys.optimization.power_balance import PowerBalance
from odys.optimization.problem import OptimizationProblem


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
        problem: OptimizationProblem,
    ) -> None:
        """Initialize the model builder with validated energy system.

        Args:
            problem: The legacy parameters and the formulations of the energy system.
        """
        self._milp_model = EnergyMILPModel(problem)
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
        for formulation in self._milp_model.problem.formulations:
            formulation.add_variables(self._milp_model.linopy_model)

        if self._milp_model.parameters.objective.term_of(CVaRTerm) is not None:
            self._add_legacy_variables(CVAR_VARIABLES)

    def _add_legacy_variables(self, variables: list[VariableDefinitionRegistry]) -> None:
        context = self._milp_model.parameters.context
        for variable in variables:
            linopy_var_params = get_linopy_variable_parameters(variable, context)
            self._milp_model.add_variable(linopy_var_params)

    def _add_model_constraints(self) -> None:
        for group in self._get_constraint_groups():
            group.add_to_model(self._milp_model.linopy_model)

    def _get_constraint_groups(self) -> list[ConstraintGroup]:
        groups: list[ConstraintGroup] = [*self._milp_model.problem.formulations, PowerBalance(self._milp_model)]

        if self._milp_model.parameters.objective.term_of(CVaRTerm) is not None:
            groups.append(CVaRConstraints(self._milp_model))

        return groups

    def _add_model_objective(self) -> None:
        objective = build_objective(self._milp_model, self._milp_model.parameters.objective)
        self._milp_model.linopy_model.add_objective(objective, sense="max")


def build_model(problem: OptimizationProblem) -> EnergyMILPModel:
    """Build the optimization model of an energy system.

    Args:
        problem: The legacy parameters and the formulations of the energy system.

    Returns:
        EnergyMILPModel ready for solving.

    """
    builder = EnergyAlgebraicModelBuilder(problem)
    return builder.build()
