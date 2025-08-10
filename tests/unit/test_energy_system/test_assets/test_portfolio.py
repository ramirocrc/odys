"""Tests for the AssetPortfolio class."""

import pytest

from optimes.energy_system.assets.base import EnergyAsset
from optimes.energy_system.assets.generator import PowerGenerator
from optimes.energy_system.assets.portfolio import AssetPortfolio
from optimes.energy_system.assets.storage import Battery


@pytest.fixture
def sample_generator_1() -> PowerGenerator:
    """Create a sample power generator for testing."""
    return PowerGenerator(
        name="test_generator_1",
        nominal_power=100.0,
        variable_cost=50.0,
    )


@pytest.fixture
def sample_generator_2() -> PowerGenerator:
    """Create a sample power generator for testing."""
    return PowerGenerator(
        name="test_generator_2",
        nominal_power=120.0,
        variable_cost=20.0,
    )


@pytest.fixture
def sample_battery() -> Battery:
    """Create a sample battery for testing."""
    return Battery(
        name="test_battery",
        capacity=100.0,
        max_power=50.0,
        efficiency_charging=0.9,
        efficiency_discharging=0.85,
        soc_initial=50.0,
    )


@pytest.fixture
def portfolio_with_assets(
    sample_generator_1: PowerGenerator,
    sample_generator_2: PowerGenerator,
    sample_battery: Battery,
) -> AssetPortfolio:
    """Create a portfolio with sample assets for testing."""
    portfolio = AssetPortfolio()
    portfolio.add_asset(sample_generator_1)
    portfolio.add_asset(sample_generator_2)
    portfolio.add_asset(sample_battery)
    return portfolio


def test_add_asset_raises_errors(
    sample_generator_1: PowerGenerator,
) -> None:
    """Test that add_asset raises appropriate errors for invalid inputs."""
    portfolio = AssetPortfolio()
    portfolio.add_asset(sample_generator_1)
    exptected_error_message = f"Asset with name '{sample_generator_1.name}' already exists."
    with pytest.raises(ValueError, match=exptected_error_message):
        portfolio.add_asset(sample_generator_1)


@pytest.mark.parametrize(
    ("asset_name", "expected_asset_type"),
    [
        ("test_generator_1", PowerGenerator),
        ("test_battery", Battery),
    ],
)
def test_get_asset_returns_correct_asset(
    asset_name: str,
    expected_asset_type: type[EnergyAsset],
    portfolio_with_assets: AssetPortfolio,
) -> None:
    """Test that get_asset returns the correct asset with proper type."""
    asset = portfolio_with_assets.get_asset(asset_name)
    assert asset.name == asset_name
    assert isinstance(asset, expected_asset_type)


def test_get_asset_raises_key_error_for_nonexistent_asset(portfolio_with_assets: AssetPortfolio) -> None:
    """Test that get_asset raises KeyError for non-existent assets."""
    with pytest.raises(KeyError, match="Asset with name 'nonexistent' does not exist."):
        portfolio_with_assets.get_asset("nonexistent")


@pytest.mark.parametrize(
    ("property_name", "expected_count", "expected_types"),
    [
        ("generators", 2, (PowerGenerator,)),
        ("batteries", 1, (Battery,)),
        ("assets", 3, (PowerGenerator, Battery)),
    ],
)
def test_portfolio_properties_return_correct_assets(
    property_name: str,
    expected_count: int,
    expected_types: tuple[type, ...],
    portfolio_with_assets: AssetPortfolio,
) -> None:
    """Test that portfolio properties return correct assets with proper types."""
    assets = getattr(portfolio_with_assets, property_name)
    assert len(assets) == expected_count

    if property_name == "assets":
        # For assets property, we get a MappingProxyType, so we need to iterate over values
        for asset in assets.values():
            assert any(isinstance(asset, asset_type) for asset_type in expected_types)

        # Test that assets property returns a read-only view
        assert hasattr(assets, "get")  # Should be a mapping-like object
        # Test that it's read-only by attempting to modify (should fail)
        with pytest.raises(TypeError):
            assets["new_key"] = "new_value"
