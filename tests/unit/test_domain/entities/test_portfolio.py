"""Tests for the AssetPortfolio class."""

from collections.abc import Callable

import pytest

from odys.domain.entities.base import Asset
from odys.domain.entities.battery import Battery
from odys.domain.entities.charger import Charger
from odys.domain.entities.electric_vehicle import ElectricVehicle
from odys.domain.entities.generator import Generator
from odys.domain.entities.market import EnergyMarket
from odys.domain.entities.portfolio import AssetPortfolio
from odys.domain.entities.stationary_storage import StationaryStorage
from odys.domain.exceptions import OdysValidationError

MARKET_VOLUME = 50.0


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
def sample_battery() -> StationaryStorage:
    """Create a sample battery for testing."""
    return StationaryStorage(
        name="test_battery",
        battery=Battery(
            capacity=100.0,
            max_charge_power=50.0,
            max_discharge_power=50.0,
            efficiency_charging=0.9,
            efficiency_discharging=0.85,
            soc_start=0.5,
        ),
    )


@pytest.fixture
def portfolio_with_assets(
    sample_generator_1: Generator,
    sample_generator_2: Generator,
    sample_battery: StationaryStorage,
) -> AssetPortfolio:
    """Create a portfolio with sample assets for testing."""
    return AssetPortfolio(assets=[sample_generator_1, sample_generator_2, sample_battery])


def test_empty_portfolio(sample_generator_1: Generator) -> None:
    """Test that creating a portfolio with duplicate assets raises an error."""
    with pytest.raises(OdysValidationError, match=r"Duplicate asset names in input"):
        AssetPortfolio(assets=[sample_generator_1, sample_generator_1])


@pytest.mark.parametrize(
    ("asset_name", "expected_asset_type"),
    [
        ("test_generator_1", Generator),
        ("test_battery", StationaryStorage),
    ],
)
def test_get_asset_returns_correct_asset(
    asset_name: str,
    expected_asset_type: type[Asset],
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


def test_assets_of_returns_assets_of_requested_type_in_insertion_order(
    sample_generator_1: Generator,
    sample_generator_2: Generator,
    sample_battery: StationaryStorage,
) -> None:
    portfolio = AssetPortfolio(assets=[sample_generator_1, sample_generator_2, sample_battery])

    generators = portfolio.assets_of(Generator)
    stationary_storages = portfolio.assets_of(StationaryStorage)
    assert sample_generator_1 is generators[0]
    assert sample_generator_2 is generators[1]
    assert sample_battery is stationary_storages[0]

    assert (generators + stationary_storages) == (sample_generator_1, sample_generator_2, sample_battery)


def test_constructor_raises_error_for_duplicate_names_in_iterable() -> None:
    """Test that the constructor raises OdysValidationError for duplicate names in the input iterable."""
    gen1 = Generator(name="same_name", nominal_power=100.0, variable_cost=50.0)
    gen2 = Generator(name="same_name", nominal_power=120.0, variable_cost=20.0)
    with pytest.raises(OdysValidationError, match=r"Duplicate asset names"):
        AssetPortfolio(assets=[gen1, gen2])


def test_empty_portfolio_is_allowed() -> None:
    """Test that an empty portfolio can be created."""
    portfolio = AssetPortfolio()
    assert len(portfolio.assets) == 0


def test_assets_of_electric_vehicle_returns_only_electric_vehicles() -> None:
    ev1 = ElectricVehicle(
        name="ev1",
        battery=Battery(capacity=50.0, max_charge_power=22.0, max_discharge_power=0.0, soc_start=0.5),
        trips=(),
    )
    ev2 = ElectricVehicle(
        name="ev2",
        battery=Battery(capacity=75.0, max_charge_power=50.0, max_discharge_power=11.0, soc_start=0.8),
        trips=(),
    )
    gen = Generator(name="gen1", nominal_power=100.0, variable_cost=20.0)
    portfolio = AssetPortfolio(assets=[ev1, ev2, gen])

    evs = portfolio.assets_of(ElectricVehicle)
    assert len(evs) == len([ev1, ev2])
    assert ev1 is evs[0]
    assert ev2 is evs[1]


def test_assets_of_charger_returns_only_chargers() -> None:
    charger1 = Charger(name="charger1", max_power=22.0)
    charger2 = Charger(name="charger2", max_power=50.0)
    gen = Generator(name="gen1", nominal_power=100.0, variable_cost=20.0)
    portfolio = AssetPortfolio(assets=[charger1, charger2, gen])

    chargers = portfolio.assets_of(Charger)
    assert len(chargers) == len([charger1, charger2])
    assert charger1 is chargers[0]
    assert charger2 is chargers[1]


def test_assets_of_absent_type_returns_empty_tuple() -> None:
    gen = Generator(name="gen1", nominal_power=100.0, variable_cost=20.0)
    portfolio = AssetPortfolio(assets=[gen])

    assert portfolio.assets_of(ElectricVehicle) == ()
    assert portfolio.assets_of(Charger) == ()


@pytest.fixture
def untyped_portfolio_factory() -> Callable[..., AssetPortfolio]:
    """AssetPortfolio as seen by a caller without type checking (the runtime guard's audience)."""
    return AssetPortfolio


def test_portfolio_rejects_market_from_untyped_caller(
    untyped_portfolio_factory: Callable[..., AssetPortfolio],
) -> None:
    gen = Generator(name="gen1", nominal_power=100.0, variable_cost=20.0)
    market = EnergyMarket(name="day_ahead", max_trading_volume_per_step=MARKET_VOLUME)
    with pytest.raises(OdysValidationError, match=r"only accepts assets.*'day_ahead'.*EnergyMarket"):
        untyped_portfolio_factory(assets=[gen, market])


def test_portfolio_keeps_all_assets_from_a_one_shot_iterable(
    sample_generator_1: Generator,
    sample_generator_2: Generator,
) -> None:
    portfolio = AssetPortfolio(assets=(generator for generator in [sample_generator_1, sample_generator_2]))
    assert portfolio.assets_of(Generator) == (sample_generator_1, sample_generator_2)
