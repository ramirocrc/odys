"""MILP model representation for energy system optimization.

This module provides the EnergyMILPModel class that wraps a linopy Model
with typed accessors for energy system decision variables.
"""

from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING

import linopy

if TYPE_CHECKING:
    from odys.optimization.model.linopy_converter import LinopyVariableParameters
    from odys.optimization.problem import OptimizationProblem
    from odys.parameters.energy_system_parameters import EnergySystemParameters


class VariableStore:
    """Typed view of the CVaR decision variables, the only ones still declared in the registry (until R3.5).

    Constructed from a linopy model after variables have been added. Field names
    are the linopy variable names from ``VariableDefinition.name``.
    """

    cvar_value_at_risk: linopy.Variable
    cvar_shortfall: linopy.Variable

    def __init__(self, linopy_model: linopy.Model) -> None:
        """Bind typed fields for variables present on the linopy model.

        Empty asset types omit their variables; accessing those fields raises
        ``AttributeError`` (same as a missing linopy key before G12).
        """
        variables = linopy_model.variables
        for var_name, var in variables.items():
            setattr(self, var_name, var)


class EnergyMILPModel:
    """Wrapper around a linopy Model with typed variable accessors for energy systems."""

    def __init__(self, problem: OptimizationProblem) -> None:
        """Initialize the MILP model for an optimization problem.

        Args:
            problem: The legacy parameters and the formulations of the energy system.

        """
        self._problem = problem
        self._parameters = problem.legacy
        self._linopy_model = linopy.Model(force_dim_names=True)

    @cached_property
    def vars(self) -> VariableStore:
        """Return the typed decision-variable view (after variables are on the linopy model)."""
        return VariableStore(self._linopy_model)

    @property
    def linopy_model(self) -> linopy.Model:
        """Return the underlying linopy model."""
        return self._linopy_model

    @property
    def problem(self) -> OptimizationProblem:
        """Return the optimization problem: the formulations, the context and the objective."""
        return self._problem

    @property
    def parameters(self) -> EnergySystemParameters:
        """Return the context and the objective (legacy container until R3.5)."""
        return self._parameters

    def add_variable(self, var_params: LinopyVariableParameters) -> None:
        """Add a variable to the underlying linopy model.

        Args:
            var_params: Parameters of the variable to add.
        """
        self.linopy_model.add_variables(
            name=var_params.name,
            coords=var_params.coords,
            lower=var_params.lower,
            binary=var_params.binary,
        )
