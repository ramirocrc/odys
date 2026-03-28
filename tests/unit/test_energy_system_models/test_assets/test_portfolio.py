"""Tests for the AssetPortfolio class."""

import pytest

from odys.energy_system_models.assets.base import EnergyAsset
from odys.energy_system_models.assets.generator import Generator
from odys.energy_system_models.assets.portfolio import AssetPortfolio
from odys.energy_system_models.assets.storage import Storage
from odys.exceptions import OdysValidationError


@pytest.fixture
def sample_generator_1() -> Generator:
    """Create a sample power generator for testing."""
    return Generator(
        name="test_generator_1",
        nominal_power=100.0,
        variable_cost=50.0,
    )


@pytest.fixture
def sample_generator_2() -> Generator:
    """Create a sample power generator for testing."""
    return Generator(
        name="test_generator_2",
        nominal_power=120.0,
        variable_cost=20.0,
    )


@pytest.fixture
def sample_battery() -> Storage:
    """Create a sample battery for testing."""
    return Storage(
        name="test_battery",
        capacity=100.0,
        max_power=50.0,
        efficiency_charging=0.9,
        efficiency_discharging=0.85,
        soc_start=0.5,
    )


@pytest.fixture
def portfolio_with_assets(
    sample_generator_1: Generator,
    sample_generator_2: Generator,
    sample_battery: Storage,
) -> AssetPortfolio:
    """Create a portfolio with sample assets for testing."""
    portfolio = AssetPortfolio()
    portfolio.add_assets(sample_generator_1)
    portfolio.add_assets(sample_generator_2)
    portfolio.add_assets(sample_battery)
    return portfolio


def test_add_asset_raises_errors(
    sample_generator_1: Generator,
) -> None:
    """Test that add_asset raises appropriate errors for invalid inputs."""
    portfolio = AssetPortfolio()
    portfolio.add_assets(sample_generator_1)
    exptected_error_message = f"Asset with name '{sample_generator_1.name}' already exists."
    with pytest.raises(OdysValidationError, match=exptected_error_message):
        portfolio.add_assets(sample_generator_1)


@pytest.mark.parametrize(
    ("asset_name", "expected_asset_type"),
    [
        ("test_generator_1", Generator),
        ("test_battery", Storage),
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
    with pytest.raises(OdysValidationError, match=r"Asset with name 'nonexistent' does not exist."):
        portfolio_with_assets.get_asset("nonexistent")


def test_portfolio_properties_return_correct_assets(
    sample_generator_1: Generator,
    sample_generator_2: Generator,
    sample_battery: Storage,
) -> None:
    portfolio = AssetPortfolio()
    portfolio.add_assets(sample_generator_1)
    portfolio.add_assets(sample_generator_2)
    portfolio.add_assets(sample_battery)

    generators = portfolio.generators
    storages = portfolio.storages
    assert sample_generator_1 is generators[0]
    assert sample_generator_2 is generators[1]
    assert sample_battery is storages[0]

    assert (generators + storages) == (sample_generator_1, sample_generator_2, sample_battery)


def test_add_assets_raises_error_for_duplicate_names_in_iterable() -> None:
    """Test that add_assets raises OdysValidationError for duplicate names in the input iterable."""
    gen1 = Generator(name="same_name", nominal_power=100.0, variable_cost=50.0)
    gen2 = Generator(name="same_name", nominal_power=120.0, variable_cost=20.0)
    portfolio = AssetPortfolio()
    with pytest.raises(OdysValidationError, match=r"Duplicate asset names"):
        portfolio.add_assets([gen1, gen2])
