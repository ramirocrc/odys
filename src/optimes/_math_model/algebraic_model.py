from typing import TypeVar, cast

import pyomo.environ as pyo
from pyomo.core.base.set import IndexedComponent

from optimes._math_model.model_components.component_protocol import PyomoComponentProtocol
from optimes._math_model.model_components.constraints import EnergyModelConstraintName
from optimes._math_model.model_components.objectives import EnergyModelObjectiveName
from optimes._math_model.model_components.parameters import EnergyModelParameterName
from optimes._math_model.model_components.sets import EnergyModelSetName
from optimes._math_model.model_components.variables import EnergyModelVariableName
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
        return cast("pyo.ConcreteModel", self._pyomo_model)

    def add_component(self, component: PyomoComponentProtocol) -> None:
        pyomo_component = component.component
        if not isinstance(component, PyomoComponentProtocol):
            msg = f"component must implement PyomoComponentProtocol, got {type(component)}"
            raise TypeError(msg)

        if not isinstance(pyomo_component, IndexedComponent):
            msg = f"Invalid .component: {pyomo_component}. Expected IndexedComponent, got {type(component.component)}"
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

        if pyomo_component.is_indexed():
            index_subsets = pyomo_component.index_set().subsets()
            index_names = [str(index) for index in index_subsets]
            if "time" in index_names and index_names[0] != "time":
                msg = (
                    f"Components indexed over 'time' should have 'time' as the first index,"
                    f" but got {component.name.value} with indices {index_names}",
                )
                raise ValueError(msg)

        setattr(self._pyomo_model, component.name.value, pyomo_component)

    def get_set(self, name: EnergyModelSetName) -> pyo.Set:
        return self._get_component(name.value, pyo.Set)

    def get_param(self, name: EnergyModelParameterName) -> pyo.Param:
        return self._get_component(name.value, pyo.Param)

    def get_var(self, name: EnergyModelVariableName) -> pyo.Var:
        return self._get_component(name.value, pyo.Var)

    def get_constraint(self, name: EnergyModelConstraintName) -> pyo.Constraint:
        return self._get_component(name.value, pyo.Constraint)

    def _get_component(self, name: str, expected_type: type[T]) -> T:
        if not hasattr(self._pyomo_model, name):
            msg = f"Component {name} does not exist in the model."
            raise AttributeError(msg)
        comp = getattr(self._pyomo_model, name)

        if not isinstance(comp, expected_type):
            msg = f"Component {name} is not a {expected_type}, got {type(comp)}."
            raise TypeError(msg)

        return comp
