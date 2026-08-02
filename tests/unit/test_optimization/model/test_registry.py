"""Tests for AssetRegistry completeness and binding."""

import pytest

from odys.optimization.constraints.constraints_group import ConstraintGroup
from odys.optimization.model.registry import AssetRegistry
from odys.optimization.parameters.parameters import EnergySystemParameters

_DISPATCHABLE_WITH_PORTS = (
    AssetRegistry.GENERATOR,
    AssetRegistry.STANDALONE_STORAGE,
    AssetRegistry.MARKET,
    AssetRegistry.FLEXIBLE_LOAD,
    AssetRegistry.ELECTRIC_VEHICLE,
)


@pytest.mark.parametrize("member", list(AssetRegistry), ids=lambda m: m.name)
def test_registry_member_has_valid_parameters_attr(member: AssetRegistry) -> None:
    assert member.spec.parameters_attr in EnergySystemParameters.model_fields


@pytest.mark.parametrize("member", list(AssetRegistry), ids=lambda m: m.name)
def test_registry_member_parameter_class_has_build(member: AssetRegistry) -> None:
    assert callable(getattr(member.spec.parameter_class, "build", None))


@pytest.mark.parametrize("member", list(AssetRegistry), ids=lambda m: m.name)
def test_registry_member_constraint_group_is_constraint_group(member: AssetRegistry) -> None:
    factory = member.spec.constraint_group
    assert isinstance(factory, type)
    assert issubclass(factory, ConstraintGroup)


def test_registry_parameters_attrs_are_unique() -> None:
    attrs = [member.spec.parameters_attr for member in AssetRegistry]
    assert len(attrs) == len(set(attrs))


def test_registry_dimensions_are_unique() -> None:
    dims = [member.spec.dimension for member in AssetRegistry]
    assert len(dims) == len(set(dims))


@pytest.mark.parametrize("member", _DISPATCHABLE_WITH_PORTS, ids=lambda m: m.name)
def test_dispatchable_assets_have_contribution_ports(member: AssetRegistry) -> None:
    assert member.spec.power_balance_terms is not None
    assert member.spec.profit_terms is not None


def test_charger_has_no_system_contributions() -> None:
    spec = AssetRegistry.CHARGER.spec
    assert spec.power_balance_terms is None
    assert spec.profit_terms is None
