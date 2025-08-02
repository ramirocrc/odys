"""Component protocol for Pyomo model components.

This module defines the PyomoComponentProtocol for ensuring consistent
interfaces across different model component types.
"""

from typing import Protocol, runtime_checkable

from pyomo.core.base.set import IndexedComponent

from optimes.math_model.model_components.constraints import EnergyModelConstraintName
from optimes.math_model.model_components.objectives import EnergyModelObjectiveName
from optimes.math_model.model_components.parameters import EnergyModelParameterName
from optimes.math_model.model_components.sets import EnergyModelSetName
from optimes.math_model.model_components.variables import EnergyModelVariableName


@runtime_checkable
class PyomoComponentProtocol(Protocol):
    """Protocol for Pyomo model components.

    This protocol defines the interface that all Pyomo model components
    must implement to be compatible with the AlgebraicModel.
    """

    @property
    def name(
        self,
    ) -> (
        EnergyModelConstraintName
        | EnergyModelObjectiveName
        | EnergyModelParameterName
        | EnergyModelSetName
        | EnergyModelVariableName
    ):
        """Get the name of the component.

        Returns:
            The component name as an appropriate enum value.
        """
        ...

    @property
    def component(self) -> IndexedComponent:
        """Get the underlying Pyomo component.

        Returns:
            The Pyomo IndexedComponent instance.
        """
        ...
