"""Tests for the AlgebraicModel class.

This module contains tests for the AlgebraicModel class which manages
Pyomo model components and provides data extraction capabilities.
"""

from unittest.mock import Mock

import pyomo.environ as pyo
import pytest

from optimes._math_model.algebraic_model import AlgebraicModel
from optimes._math_model.model_components.component_protocol import PyomoComponentProtocol
from optimes._math_model.model_components.parameters import EnergyModelParameterName, SystemParameter
from optimes._math_model.model_components.sets import EnergyModelSetName, SystemSet
from optimes._math_model.model_components.variables import EnergyModelVariableName, SystemVariable


class TestAlgebraicModel:
    """Test cases for the AlgebraicModel class."""

    def test_pyomo_model_property(self) -> None:
        """Test the pyomo_model property returns the correct model."""
        model = AlgebraicModel()
        pyomo_model = model.pyomo_model
        assert isinstance(pyomo_model, pyo.ConcreteModel)
        assert pyomo_model is model._pyomo_model  # noqa: SLF001

    def test_add_get_valid_components(self) -> None:
        """Test adding a valid set component."""
        model = AlgebraicModel()

        time_set = pyo.Set()
        component_set = SystemSet(name=EnergyModelSetName.TIME, component=time_set)

        param = pyo.Param()
        component_param = SystemParameter(name=EnergyModelParameterName.DEMAND, component=param)

        var = pyo.Var()
        component_var = SystemVariable(name=EnergyModelVariableName.GENERATOR_POWER, component=var)

        model.add_component(component_set)
        model.add_component(component_param)
        model.add_component(component_var)

        assert model.get_set(EnergyModelSetName.TIME) is time_set
        assert model.get_param(EnergyModelParameterName.DEMAND) is param
        assert model.get_var(EnergyModelVariableName.GENERATOR_POWER) is var

    def test_add_component_invalid_component_type(self) -> None:
        """Test that add_component raises TypeError for invalid component.component type."""
        model = AlgebraicModel()
        invalid_component = Mock(spec=PyomoComponentProtocol)
        invalid_component.component = "not_an_indexed_component"
        invalid_component.name = EnergyModelSetName.TIME

        with pytest.raises(TypeError, match="Invalid .component: not_an_indexed_component"):
            model.add_component(invalid_component)

    def test_add_component_invalid_name_type(self) -> None:
        """Test that add_component raises TypeError for invalid component name type."""
        model = AlgebraicModel()
        invalid_component = Mock(spec=PyomoComponentProtocol)
        invalid_component.component = pyo.Set()
        invalid_component.name = "invalid_name"

        with pytest.raises(TypeError, match="Invalid .name: invalid_name"):
            model.add_component(invalid_component)

    def test_add_component_duplicate_name(self) -> None:
        """Test that add_component raises AttributeError for duplicate component names."""
        model = AlgebraicModel()
        component = SystemSet(name=EnergyModelSetName.TIME, component=pyo.Set())
        model.add_component(component)

        with pytest.raises(AttributeError, match="Component EnergyModelSetName.TIME already exists"):
            model.add_component(component)

    def test_add_component_time_index_validation(self) -> None:
        """Test that add_component validates time index position correctly."""
        model = AlgebraicModel()
        generators_set = pyo.Set(initialize=["gen1", "gen2"], name="generators")
        time_set = pyo.Set(initialize=[1, 2, 3], name="time")

        var = pyo.Var(generators_set, time_set, name="var_generator_power")
        component = SystemVariable(name=EnergyModelVariableName.GENERATOR_POWER, component=var)
        with pytest.raises(ValueError, match="Components indexed over 'time' should have 'time' as the first index"):
            model.add_component(component)

    def test_get_set_not_found(self) -> None:
        """Test that get_set raises AttributeError for non-existent set."""
        model = AlgebraicModel()

        with pytest.raises(AttributeError, match="Component time does not exist"):
            model.get_set(EnergyModelSetName.TIME)

        with pytest.raises(AttributeError, match="Component param_demand does not exist"):
            model.get_param(EnergyModelParameterName.DEMAND)

        with pytest.raises(AttributeError, match="Component var_generator_power does not exist"):
            model.get_var(EnergyModelVariableName.GENERATOR_POWER)
