from enum import Enum
from typing import TYPE_CHECKING, TypeVar, cast

import pandas as pd
import pyomo.environ as pyo
from pyomo.core.base.set import IndexedComponent

from optimes._math_model.model_components.component_protocol import PyomoComponentProtocol
from optimes._math_model.model_components.constraints import EnergyModelConstraintName
from optimes._math_model.model_components.objectives import EnergyModelObjectiveName
from optimes._math_model.model_components.parameters import EnergyModelParameterName
from optimes._math_model.model_components.sets import EnergyModelSetName
from optimes._math_model.model_components.variables import EnergyModelVariableName
from optimes.utils.logging import get_logger

if TYPE_CHECKING:
    from pyomo.core.base.var import IndexedVar

logger = get_logger(__name__)

ALLOWED_COMPONENT_NAME_TYPES = (
    EnergyModelConstraintName,
    EnergyModelObjectiveName,
    EnergyModelParameterName,
    EnergyModelSetName,
    EnergyModelVariableName,
)

T = TypeVar("T", bound=IndexedComponent)


class ResultDfDirection(Enum):
    HORIZONTAL = "horizontal"
    VERTICAL = "vertical"


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

    def _get_component(self, name: str, expected_type: type[T]) -> T:
        if not hasattr(self._pyomo_model, name):
            msg = f"Component {name} does not exist in the model."
            raise AttributeError(msg)
        comp = getattr(self._pyomo_model, name)

        if not isinstance(comp, expected_type):
            msg = f"Component {name} is not a {expected_type}, got {type(comp)}."
            raise TypeError(msg)

        return comp

    def to_dataframe(self, direction: str) -> pd.DataFrame:
        parsed_direction = ResultDfDirection(direction)
        if parsed_direction == ResultDfDirection.HORIZONTAL:
            return self._get_horizonal_dataframe
        return self._get_vertical_dataframe

    @property
    def _get_horizonal_dataframe(self) -> pd.DataFrame:
        aggregated_variables_data = {}
        for variable in self.pyomo_model.component_objects(pyo.Var, active=True):
            variable = cast("IndexedVar", variable)
            first_index_set, _ = variable.index_set().subsets()
            if first_index_set.name != "time":
                msg = f"Expected first index set of variable to be 'time', got {first_index_set.name} instead"
                raise ValueError(msg)
            var_name = variable.name
            data = []
            for idx in variable:
                if idx is None:
                    msg = "Index cannot be None"
                    raise ValueError(msg)
                time, unit = idx
                val = variable[idx].value
                data.append((time, unit, val))

            variable_data = pd.DataFrame(data, columns=["time", "unit", "value"])  # pyright: ignore reportArgumentType
            aggregated_variables_data[var_name] = variable_data.pivot_table(
                index="time",
                columns="unit",
                values="value",
            )
        return pd.concat(aggregated_variables_data, axis=1)

    @property
    def _get_vertical_dataframe(self) -> pd.DataFrame:
        records = []
        for variable in self.pyomo_model.component_objects(pyo.Var, active=True):
            variable = cast("IndexedVar", variable)
            first_index_set, _ = variable.index_set().subsets()
            if first_index_set.name != "time":
                msg = f"Expected first index set to be 'time', got {first_index_set.name}"
                raise ValueError(msg)
            var_name = variable.name
            for idx in variable:
                if idx is None:
                    msg = "Index cannot be None"
                    raise ValueError(msg)
                time, unit = idx
                val = variable[idx].value
                records.append({"unit": unit, "variable": var_name, "time": time, "value": val})
        df = pd.DataFrame.from_records(records)
        return df.sort_values(["unit", "variable", "time"]).reset_index(drop=True)
