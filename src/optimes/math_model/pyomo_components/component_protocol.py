from typing import Protocol

from pyomo.core.base.set import IndexedComponent

from optimes.math_model.pyomo_components.constraints import EnergyModelConstraintName
from optimes.math_model.pyomo_components.objectives import EnergyModelObjectiveName
from optimes.math_model.pyomo_components.parameters import EnergyModelParameterName
from optimes.math_model.pyomo_components.sets import EnergyModelSetName
from optimes.math_model.pyomo_components.variables import EnergyModelVariableName


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
