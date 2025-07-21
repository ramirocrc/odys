import pyomo.environ as pyo
from pyomo.core.base.set import ComponentData, IndexedComponent

from optimes.math_model.pyomo_components.component_protocol import PyomoComponentProtocol
from optimes.math_model.pyomo_components.parameters import EnergyModelParameterName
from optimes.math_model.pyomo_components.sets import EnergyModelSetName
from optimes.math_model.pyomo_components.variables import EnergyModelVariableName
from optimes.utils.logging import get_logger

logger = get_logger(__name__)


class ExtendedPyomoModel(pyo.ConcreteModel):
    def new_component(self, component: PyomoComponentProtocol) -> None:
        if hasattr(self, component.name.value):
            msg = f"Component {component.name} already exists in the model."
            raise AttributeError(msg)
        if not isinstance(component.component, IndexedComponent):
            msg = f"Expected IndexedComponent, got {type(component.component)}"
            raise TypeError(msg)
        setattr(self, component.name.value, component.component)

    def __getitem__(
        self,
        name: EnergyModelVariableName | EnergyModelParameterName | EnergyModelSetName,
    ) -> ComponentData:
        if not hasattr(self, name.value):
            msg = f"Component {name.value} does not exist in the model."
            raise AttributeError(msg)
        return getattr(self, name.value)
