from typing import Protocol, runtime_checkable

from pyomo.core.base.set import IndexedComponent

from optimes._math_model.model_components.constraints import EnergyModelConstraintName
from optimes._math_model.model_components.objectives import EnergyModelObjectiveName
from optimes._math_model.model_components.parameters import EnergyModelParameterName
from optimes._math_model.model_components.sets import EnergyModelSetName
from optimes._math_model.model_components.variables import EnergyModelVariableName


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
    ): ...

    @property
    def component(self) -> IndexedComponent: ...
