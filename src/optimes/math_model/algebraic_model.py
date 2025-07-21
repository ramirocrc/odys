import pyomo.environ as pyo
from pyomo.core.base.set import IndexedComponent

from optimes.math_model.model_components.component_protocol import PyomoComponentProtocol
from optimes.math_model.model_components.parameters import EnergyModelParameterName
from optimes.math_model.model_components.sets import EnergyModelSetName
from optimes.math_model.model_components.variables import EnergyModelVariableName
from optimes.utils.logging import get_logger

logger = get_logger(__name__)


class AlgebraicModel(pyo.ConcreteModel):
    def new_component(self, component: PyomoComponentProtocol) -> None:
        if hasattr(self, component.name.value):
            msg = f"Component {component.name} already exists in the model."
            raise AttributeError(msg)
        if not isinstance(component.component, IndexedComponent):
            msg = f"Expected IndexedComponent, got {type(component.component)}"
            raise TypeError(msg)
        setattr(self, component.name.value, component.component)

    # TODO: to implemnet get_param, get_var, get_set instead
    def __getitem__(  # type: ignore reportIncompatibleMethodOverride
        self,
        name: EnergyModelVariableName | EnergyModelParameterName | EnergyModelSetName,
    ) -> IndexedComponent:
        if not hasattr(self, name.value):
            msg = f"Component {name.value} does not exist in the model."
            raise AttributeError(msg)
        component = getattr(self, name.value)
        if not isinstance(component, IndexedComponent):
            msg = f"Expected {name} to be of type ComponentData, got {type(component)} instead"
            raise TypeError(msg)

        return component
