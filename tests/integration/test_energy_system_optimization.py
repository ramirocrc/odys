from collections.abc import Callable
from dataclasses import dataclass
from datetime import timedelta

import pandas as pd
import pytest

from odis.energy_system import EnergySystem
from odis.energy_system_models.assets.base import EnergyAsset
from odis.energy_system_models.assets.generator import PowerGenerator
from odis.energy_system_models.assets.load import Load
from odis.energy_system_models.assets.portfolio import AssetPortfolio
from odis.energy_system_models.assets.storage import Battery
from odis.energy_system_models.markets import EnergyMarket
from odis.energy_system_models.scenarios import Scenario
from odis.energy_system_models.units import PowerUnit

STANDARD_GENERATOR_POWER = 100.0
LARGE_GENERATOR_POWER = 200.0

CHEAP_COST = 20.0
MEDIUM_COST = 25.0
EXPENSIVE_COST = 30.0
VERY_EXPENSIVE_COST = 40.0

STANDARD_BATTERY_CAPACITY = 100.0

PERFECT_EFFICIENCY = 1.0
HALF_EFFICIENCY = 0.5

SIMPLE_LOAD_PROFILE = [50.0, 100.0, 150.0, 180.0, 120.0]
RAMPING_LOAD_PROFILE = [50.0, 100.0, 150.0, 200.0, 250.0, 300.0]
STORAGE_TEST_PROFILE = [50.0, 50.0, 150.0, 150.0, 50.0]
SHORT_STORAGE_PROFILE = [50.0, 50.0, 100.0]

MARKET_HIGH_PRICES = [50.0, 60.0, 55.0]
MARKET_LOW_PRICES = [25.0, 30.0, 28.0]


@pytest.fixture
def standard_load() -> Load:
    """Standard load fixture for reuse across tests."""
    return Load(name="load1")


@pytest.fixture
def cheap_generator() -> PowerGenerator:
    """Cheap generator fixture."""
    return PowerGenerator(
        name="generator_100mw_cheap",
        nominal_power=STANDARD_GENERATOR_POWER,
        variable_cost=CHEAP_COST,
    )


@pytest.fixture
def medium_generator() -> PowerGenerator:
    """Medium cost generator fixture."""
    return PowerGenerator(
        name="generator_100mw_medium",
        nominal_power=STANDARD_GENERATOR_POWER,
        variable_cost=EXPENSIVE_COST,
    )


@pytest.fixture
def expensive_generator() -> PowerGenerator:
    """Expensive generator fixture."""
    return PowerGenerator(
        name="generator_100mw_expensive",
        nominal_power=STANDARD_GENERATOR_POWER,
        variable_cost=VERY_EXPENSIVE_COST,
    )


@pytest.fixture
def perfect_battery() -> Battery:
    """Battery with perfect efficiency fixture."""
    return Battery(
        name="energy_storage",
        capacity=STANDARD_BATTERY_CAPACITY,
        max_power=STANDARD_GENERATOR_POWER,
        efficiency_charging=PERFECT_EFFICIENCY,
        efficiency_discharging=PERFECT_EFFICIENCY,
        soc_start=0.0,
        soc_end=50.0,
    )


@dataclass
class LoadProfile:
    """Container for load profile data with metadata."""

    values: list[float]
    description: str

    def __len__(self) -> int:
        return len(self.values)


@dataclass
class SystemTestCase:
    """Container for test system components and expected results."""

    energy_system: EnergySystem
    expected_generator_results: pd.DataFrame | None = None
    expected_battery_results: pd.DataFrame | None = None
    description: str = ""


def _create_time_index(num_steps: int) -> pd.Index:
    """Create a proper time index for test DataFrames."""
    return pd.Index([str(i) for i in range(num_steps)], name="time")


def _create_expected_dataframe(
    data: dict[str, list[float]],
    num_steps: int,
    column_name: str,
) -> pd.DataFrame:
    """Create expected results DataFrame with consistent formatting."""
    df = pd.DataFrame(data, index=_create_time_index(num_steps))
    df.columns.name = column_name
    return df


def _create_energy_system(
    assets: list[EnergyAsset],
    load_profile: list[float],
    load: Load,
    markets: list[EnergyMarket] | None = None,
    market_prices: dict[str, list[float]] | None = None,
) -> EnergySystem:
    """Create energy system with common setup logic."""
    portfolio = AssetPortfolio()
    for asset in assets:
        portfolio.add_asset(asset)

    portfolio.add_asset(load)

    return EnergySystem(
        portfolio=portfolio,
        markets=markets,
        timestep=timedelta(hours=1),
        number_of_steps=len(load_profile),
        power_unit=PowerUnit.MegaWatt,
        scenarios=Scenario(
            available_capacity_profiles={},
            load_profiles={load.name: load_profile},
            market_prices=market_prices,
        ),
    )


def _create_single_generator_system() -> SystemTestCase:
    """Create a system with a single generator that meets all load.

    Tests basic optimization where one generator with sufficient capacity
    serves the entire load profile.
    """
    generator = PowerGenerator(
        name="gen1",
        nominal_power=LARGE_GENERATOR_POWER,
        variable_cost=EXPENSIVE_COST,
    )

    load = Load(name="load1")
    energy_system = _create_energy_system([generator], SIMPLE_LOAD_PROFILE, load)

    expected_generator_results = _create_expected_dataframe(
        {"gen1": SIMPLE_LOAD_PROFILE},
        len(SIMPLE_LOAD_PROFILE),
        "generator",
    )

    return SystemTestCase(
        energy_system,
        expected_generator_results=expected_generator_results,
        description="Single generator serves variable load",
    )


def _create_three_generators_system() -> SystemTestCase:
    """Create a system with three generators of different costs.

    Tests merit order dispatch where cheaper generators are used first,
    then more expensive ones as load increases.
    """
    generator_cheap = PowerGenerator(
        name="generator_100mw_cheap",
        nominal_power=STANDARD_GENERATOR_POWER,
        variable_cost=CHEAP_COST,
    )
    generator_medium = PowerGenerator(
        name="generator_100mw_medium",
        nominal_power=STANDARD_GENERATOR_POWER,
        variable_cost=EXPENSIVE_COST,
    )
    generator_expensive = PowerGenerator(
        name="generator_100mw_expensive",
        nominal_power=STANDARD_GENERATOR_POWER,
        variable_cost=VERY_EXPENSIVE_COST,
    )

    load = Load(name="load1")
    energy_system = _create_energy_system(
        [generator_cheap, generator_medium, generator_expensive],
        RAMPING_LOAD_PROFILE,
        load,
    )

    expected_generator_results = _create_expected_dataframe(
        {
            generator_cheap.name: [50.0, 100.0, 100.0, 100.0, 100.0, 100.0],
            generator_medium.name: [0.0, 0.0, 50.0, 100.0, 100.0, 100.0],
            generator_expensive.name: [0.0, 0.0, 0.0, 0.0, 50.0, 100.0],
        },
        len(RAMPING_LOAD_PROFILE),
        "generator",
    )

    return SystemTestCase(
        energy_system,
        expected_generator_results=expected_generator_results,
        description="Merit order dispatch with three generators",
    )


def _create_generator_and_battery_system() -> SystemTestCase:
    """Create a system with a generator and battery with perfect efficiency.

    Tests energy storage optimization where battery stores excess generation
    during low load and discharges during high demand periods.
    """
    generator = PowerGenerator(
        name="base_generator",
        nominal_power=STANDARD_GENERATOR_POWER,
        variable_cost=MEDIUM_COST,
    )
    battery = Battery(
        name="energy_storage",
        capacity=STANDARD_BATTERY_CAPACITY,
        max_power=STANDARD_GENERATOR_POWER,
        efficiency_charging=PERFECT_EFFICIENCY,
        efficiency_discharging=PERFECT_EFFICIENCY,
        soc_start=0.0,
        soc_end=50.0,
    )

    load = Load(name="load1")
    energy_system = _create_energy_system([generator, battery], STORAGE_TEST_PROFILE, load)

    expected_generator_results = _create_expected_dataframe(
        {generator.name: [100.0, 100.0, 100.0, 100.0, 100.0]},
        len(STORAGE_TEST_PROFILE),
        "generator",
    )

    expected_battery_results = _create_expected_dataframe(
        {battery.name: [50.0, 100.0, 50.0, 0.0, 50.0]},
        len(STORAGE_TEST_PROFILE),
        "battery",
    )

    return SystemTestCase(
        energy_system,
        expected_generator_results=expected_generator_results,
        expected_battery_results=expected_battery_results,
        description="Generator with perfect efficiency battery storage",
    )


def _create_generator_and_battery_with_efficiencies_system() -> SystemTestCase:
    """Create a system with a generator and battery with efficiency losses.

    Tests energy storage optimization with realistic efficiency losses,
    demonstrating how charging/discharging inefficiencies affect the solution.
    """
    generator = PowerGenerator(
        name="generator",
        nominal_power=STANDARD_GENERATOR_POWER,
        variable_cost=MEDIUM_COST,
    )
    battery = Battery(
        name="battery",
        capacity=STANDARD_BATTERY_CAPACITY,
        max_power=STANDARD_GENERATOR_POWER,
        efficiency_charging=HALF_EFFICIENCY,
        efficiency_discharging=HALF_EFFICIENCY,
        soc_start=0.0,
        soc_end=50.0,
    )

    load = Load(name="load1")
    energy_system = _create_energy_system([generator, battery], SHORT_STORAGE_PROFILE, load)

    expected_generator_results = _create_expected_dataframe(
        {generator.name: [100.0, 100.0, 100.0]},
        len(SHORT_STORAGE_PROFILE),
        "generator",
    )

    expected_battery_results = _create_expected_dataframe(
        {battery.name: [25.0, 50.0, 50.0]},
        len(SHORT_STORAGE_PROFILE),
        "battery",
    )

    return SystemTestCase(
        energy_system,
        expected_generator_results=expected_generator_results,
        expected_battery_results=expected_battery_results,
        description="Generator with battery efficiency losses",
    )


def _create_generator_load_and_market_system() -> SystemTestCase:
    """Create a system with a generator, load, and market.

    Tests market participation where excess generation can be sold
    and the optimizer balances generation cost vs market revenue.
    """
    generator = PowerGenerator(
        name="market_generator",
        nominal_power=STANDARD_GENERATOR_POWER,
        variable_cost=EXPENSIVE_COST,
    )

    market = EnergyMarket(
        name="energy_market",
        max_trading_volume_per_step=STANDARD_GENERATOR_POWER,
    )

    load = Load(name="load1")
    load_profile = [50.0, 75.0, 100.0]

    energy_system = _create_energy_system(
        [generator],
        load_profile,
        load,
        markets=[market],
        market_prices={"energy_market": MARKET_HIGH_PRICES},
    )

    expected_generator_results = _create_expected_dataframe(
        {"market_generator": [100.0, 100.0, 100.0]},
        len(load_profile),
        "generator",
    )

    return SystemTestCase(
        energy_system,
        expected_generator_results=expected_generator_results,
        description="Generator with load and high-price market",
    )


def _create_generator_and_two_markets_system() -> SystemTestCase:
    """Create a system with a generator and two markets.

    Tests market arbitrage where the optimizer chooses between
    selling to different markets based on price differences.
    """
    generator = PowerGenerator(
        name="arbitrage_generator",
        nominal_power=STANDARD_GENERATOR_POWER,
        variable_cost=CHEAP_COST,
    )

    cheap_market = EnergyMarket(
        name="cheap_market",
        max_trading_volume_per_step=50.0,
    )
    expensive_market = EnergyMarket(
        name="expensive_market",
        max_trading_volume_per_step=50.0,
    )

    load = Load(name="load1")
    load_profile = [30.0, 40.0, 50.0]

    energy_system = _create_energy_system(
        [generator],
        load_profile,
        load,
        markets=[cheap_market, expensive_market],
        market_prices={
            "cheap_market": MARKET_LOW_PRICES,
            "expensive_market": MARKET_HIGH_PRICES,
        },
    )

    expected_generator_results = _create_expected_dataframe(
        {"arbitrage_generator": [100.0, 100.0, 100.0]},
        len(load_profile),
        "generator",
    )

    return SystemTestCase(
        energy_system,
        expected_generator_results=expected_generator_results,
        description="Generator with two markets of different prices",
    )


def _create_market_only_system() -> SystemTestCase:
    """Create a system with only a market and load (no generators).

    Tests market purchasing where all load demand must be met
    by buying energy from the market at market prices.
    """
    market = EnergyMarket(
        name="energy_market",
        max_trading_volume_per_step=200.0,
    )

    load = Load(name="load1")
    load_profile = [40.0, 50.0, 60.0]

    energy_system = _create_energy_system(
        [],
        load_profile,
        load,
        markets=[market],
        market_prices={"energy_market": MARKET_LOW_PRICES},
    )

    return SystemTestCase(
        energy_system,
        description="Market only system with single load",
    )


@pytest.mark.parametrize(
    ("test_id", "system_factory"),
    [
        (
            "single_generator_meets_load",
            _create_single_generator_system,
        ),
        (
            "three_generators_meet_load",
            _create_three_generators_system,
        ),
        ("generator_and_battery_optimization", _create_generator_and_battery_system),
        (
            "generator_and_battery_with_efficiencies_optimization",
            _create_generator_and_battery_with_efficiencies_system,
        ),
        (
            "generator_load_and_market_optimization",
            _create_generator_load_and_market_system,
        ),
        (
            "generator_and_two_markets_optimization",
            _create_generator_and_two_markets_system,
        ),
        (
            "market_only_optimization",
            _create_market_only_system,
        ),
    ],
)
def test_energy_system_optimization(test_id: str, system_factory: Callable[[], SystemTestCase]) -> None:
    """Test energy system optimization scenarios.

    Args:
        test_id: Unique identifier for the test case
        system_factory: Factory function that creates the test system
    """

    test_system = system_factory()

    result = test_system.energy_system.optimize()

    assert result.solver_status == "ok", f"Solver failed for {test_id}"
    assert result.termination_condition == "optimal", f"Non-optimal solution for {test_id}"

    if test_system.expected_generator_results is not None:
        pd.testing.assert_frame_equal(
            result.generators.power,
            test_system.expected_generator_results,
            check_names=True,
        )

    if test_system.expected_battery_results is not None:
        pd.testing.assert_frame_equal(
            result.batteries.state_of_charge,
            test_system.expected_battery_results,
            check_names=True,
        )
