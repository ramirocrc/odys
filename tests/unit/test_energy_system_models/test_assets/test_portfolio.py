"""Tests for the AssetPortfolio class."""

import pytest

from optimes.energy_system_models.assets.base import EnergyAsset
from optimes.energy_system_models.assets.generator import PowerGenerator
from optimes.energy_system_models.assets.portfolio import AssetPortfolio
from optimes.energy_system_models.assets.storage import Battery


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
        soc_start=50.0,
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
    with pytest.raises(KeyError, match=r"Asset with name 'nonexistent' does not exist."):
        portfolio_with_assets.get_asset("nonexistent")


def test_portfolio_properties_return_correct_assets(
    sample_generator_1: PowerGenerator,
    sample_generator_2: PowerGenerator,
    sample_battery: Battery,
) -> None:
    portfolio = AssetPortfolio()
    portfolio.add_asset(sample_generator_1)
    portfolio.add_asset(sample_generator_2)
    portfolio.add_asset(sample_battery)

    generators = portfolio.generators
    batteries = portfolio.batteries
    assert sample_generator_1 is generators[0]
    assert sample_generator_2 is generators[1]
    assert sample_battery is batteries[0]

    assert (generators + batteries) == (sample_generator_1, sample_generator_2, sample_battery)
