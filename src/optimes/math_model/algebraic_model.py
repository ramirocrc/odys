from typing import TypeVar

import pyomo.environ as pyo
from pyomo.core.base.set import IndexedComponent

from optimes.math_model.model_components.component_protocol import PyomoComponentProtocol
from optimes.math_model.model_components.constraints import EnergyModelConstraintName
from optimes.math_model.model_components.objectives import EnergyModelObjectiveName
from optimes.math_model.model_components.parameters import EnergyModelParameterName
from optimes.math_model.model_components.sets import EnergyModelSetName
from optimes.math_model.model_components.variables import EnergyModelVariableName
from optimes.utils.logging import get_logger

logger = get_logger(__name__)

ALLOWED_COMPONENT_NAME_TYPES = (
    EnergyModelConstraintName,
    EnergyModelObjectiveName,
    EnergyModelParameterName,
    EnergyModelSetName,
    EnergyModelVariableName,
)

T = TypeVar("T", bound=IndexedComponent)


class AlgebraicModel:
    def __init__(self) -> None:
        self._pyomo_model = pyo.ConcreteModel()

    @property
    def pyomo_model(self) -> pyo.ConcreteModel:
        if not isinstance(self._pyomo_model, pyo.ConcreteModel):
            msg = f"Expected .pyomo_model to be pyo.ConcreteModel, got {type(self._pyomo_model)}"
            raise TypeError(msg)

        return self._pyomo_model

    def add_component(self, component: PyomoComponentProtocol) -> None:
        if not isinstance(component, PyomoComponentProtocol):
            msg = f"component must implement PyomoComponentProtocol, got {type(component)}"
            raise TypeError(msg)

        if not isinstance(component.component, IndexedComponent):
            msg = (
                f"Invalid .component: {component.component}. Expected IndexedComponent, got {type(component.component)}"
            )
            raise TypeError(msg)

        if not isinstance(component.name, ALLOWED_COMPONENT_NAME_TYPES):
            msg = (
                f"Invalid .name: {component.name}. "
                f"Expected instance of one of {ALLOWED_COMPONENT_NAME_TYPES}, got {type(component.name)}"
            )
            raise TypeError(msg)

        if hasattr(self._pyomo_model, component.name.value):
            msg = f"Component {component.name} already exists in the model."
            raise AttributeError(msg)

        setattr(self._pyomo_model, component.name.value, component.component)

    def get_set(self, name: EnergyModelSetName) -> pyo.Set:
        return self._get_component(name.value, pyo.Set)

    def get_param(self, name: EnergyModelParameterName) -> pyo.Param:
        return self._get_component(name.value, pyo.Param)

    def get_var(self, name: EnergyModelVariableName) -> pyo.Var:
        return self._get_component(name.value, pyo.Var)

    def _get_component(self, name: str, expected_type: type[T]) -> T:
        if not hasattr(self._pyomo_model, name):
            msg = f"Component {name} does not exist in the model."
            raise AttributeError(msg)
        comp = getattr(self._pyomo_model, name)

        if not isinstance(comp, expected_type):
            msg = f"Component {name} is not a {expected_type}, got {type(comp)}."
            raise TypeError(msg)

        return comp
