"""Algebraic model implementation for energy system optimization.

This module provides the AlgebraicModel class for building and managing
Pyomo models with proper component organization and validation.
"""

from typing import TYPE_CHECKING, TypeVar, cast

import pandas as pd
import pyomo.environ as pyo
from pyomo.core.base.set import IndexedComponent

from optimes.math_model.model_components.component_protocol import PyomoComponentProtocol
from optimes.math_model.model_components.constraints import EnergyModelConstraintName
from optimes.math_model.model_components.objectives import EnergyModelObjectiveName
from optimes.math_model.model_components.parameters import EnergyModelParameterName
from optimes.math_model.model_components.sets import EnergyModelSetName
from optimes.math_model.model_components.variables import EnergyModelVariableName
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


class AlgebraicModel:
    """A wrapper around Pyomo models for energy system optimization.

    This class provides a structured interface for building and managing
    Pyomo models with proper component organization and validation.
    """

    def __init__(self) -> None:
        """Initialize an empty algebraic model with a Pyomo concrete model."""
        self._pyomo_model = pyo.ConcreteModel()

    @property
    def pyomo_model(self) -> pyo.ConcreteModel:
        """Get the underlying Pyomo concrete model.

        Returns:
            The Pyomo concrete model instance.

        Raises:
            TypeError: If the model is not a Pyomo concrete model.

        """
        if not isinstance(self._pyomo_model, pyo.ConcreteModel):
            msg = f"Expected .pyomo_model to be pyo.ConcreteModel, got {type(self._pyomo_model)}"
            raise TypeError(msg)

        return self._pyomo_model

    def add_component(self, component: PyomoComponentProtocol) -> None:
        """Add a component to the algebraic model.

        Args:
            component: The component to add to the model.

        Raises:
            TypeError: If the component doesn't implement PyomoComponentProtocol
                or if the component is not an IndexedComponent.
            AttributeError: If a component with the same name already exists.
            ValueError: If time-indexed components don't have time as the first index.

        """
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
        """Get a set component from the model.

        Args:
            name: The name of the set to retrieve.

        Returns:
            The Pyomo set component.

        Raises:
            AttributeError: If the set doesn't exist in the model.
            TypeError: If the component is not a Pyomo set.

        """
        return self._get_component(name.value, pyo.Set)

    def get_param(self, name: EnergyModelParameterName) -> pyo.Param:
        """Get a parameter component from the model.

        Args:
            name: The name of the parameter to retrieve.

        Returns:
            The Pyomo parameter component.

        Raises:
            AttributeError: If the parameter doesn't exist in the model.
            TypeError: If the component is not a Pyomo parameter.

        """
        return self._get_component(name.value, pyo.Param)

    def get_var(self, name: EnergyModelVariableName) -> pyo.Var:
        """Get a variable component from the model.

        Args:
            name: The name of the variable to retrieve.

        Returns:
            The Pyomo variable component.

        Raises:
            AttributeError: If the variable doesn't exist in the model.
            TypeError: If the component is not a Pyomo variable.

        """
        return self._get_component(name.value, pyo.Var)

    def _get_component(self, name: str, expected_type: type[T]) -> T:
        """Get a component from the model with type checking.

        Args:
            name: The name of the component to retrieve.
            expected_type: The expected type of the component.

        Returns:
            The component of the expected type.

        Raises:
            AttributeError: If the component doesn't exist in the model.
            TypeError: If the component is not of the expected type.

        """
        if not hasattr(self._pyomo_model, name):
            msg = f"Component {name} does not exist in the model."
            raise AttributeError(msg)
        comp = getattr(self._pyomo_model, name)

        if not isinstance(comp, expected_type):
            msg = f"Component {name} is not a {expected_type}, got {type(comp)}."
            raise TypeError(msg)

        return comp

    @property
    def to_dataframe(self) -> pd.DataFrame:
        """Convert model variables to a pandas DataFrame.

        Returns:
            DataFrame with variables as columns and time periods as rows.
            Each variable is represented as a multi-level column with
            the variable name and unit name.

        Raises:
            ValueError: If variables are not properly indexed over time.

        """
        aggregated_variables_data = {}
        for variable in self.pyomo_model.component_objects(pyo.Var, active=True):
            variable = cast("IndexedVar", variable)
            first_index_set, _ = variable.index_set().subsets()
            if first_index_set.name != "time":
                msg = f"Expected first index set of variable to be 'time', got {first_index_set.name} instead"
                raise ValueError(msg)
            var_name = variable.name
            # collect (time, unit, value) for each indexed entry
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
