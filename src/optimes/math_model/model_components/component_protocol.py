from typing import Protocol, runtime_checkable

from pyomo.core.base.set import IndexedComponent

from optimes.math_model.model_components.constraints import EnergyModelConstraintName
from optimes.math_model.model_components.objectives import EnergyModelObjectiveName
from optimes.math_model.model_components.parameters import EnergyModelParameterName
from optimes.math_model.model_components.sets import EnergyModelSetName
from optimes.math_model.model_components.variables import EnergyModelVariableName


@runtime_checkable
class PyomoComponentProtocol(Protocol):
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
