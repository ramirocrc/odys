"""Tests for energy system input validation functions."""

import pytest

from odys.energy_system_models.assets.generator import Generator
from odys.energy_system_models.assets.load import Load
from odys.energy_system_models.assets.portfolio import AssetPortfolio
from odys.energy_system_models.assets.storage import Storage
from odys.energy_system_models.markets import EnergyMarket
from odys.energy_system_models.scenarios import StochasticScenario
from odys.energy_system_models.validation import (
    validate_available_capacity_profiles,
    validate_enough_energy_to_meet_demand,
    validate_enough_power_to_meet_demand,
    validate_load_profiles,
    validate_loads_consistent_with_scenarios,
    validate_markets_consistent_with_scenarios,
)
from odys.exceptions import OdysValidationError

NOMINAL_POWER = 100.0
VARIABLE_COST = 50.0
STORAGE_CAPACITY = 50.0
STORAGE_MAX_POWER = 25.0
STORAGE_EFFICIENCY = 0.9
SOC_START = 0.5
MAX_TRADING_VOLUME = 100.0
NUMBER_OF_STEPS = 4
SCENARIO_PROBABILITY = 1.0
DEMAND_PROFILE = [80.0, 120.0, 90.0, 100.0]
MARKET_PRICES = [10.0, 20.0, 30.0, 40.0]


@pytest.fixture
def generator() -> Generator:
    return Generator(name="gen1", nominal_power=NOMINAL_POWER, variable_cost=VARIABLE_COST)


@pytest.fixture
def storage() -> Storage:
    return Storage(
        name="bat1",
        capacity=STORAGE_CAPACITY,
        max_power=STORAGE_MAX_POWER,
        efficiency_charging=STORAGE_EFFICIENCY,
        efficiency_discharging=STORAGE_EFFICIENCY,
        soc_start=SOC_START,
    )


@pytest.fixture
def load() -> Load:
    return Load(name="load1")


@pytest.fixture
def portfolio(generator: Generator, storage: Storage, load: Load) -> AssetPortfolio:
    p = AssetPortfolio()
    p.add_assets([generator, storage, load])
    return p


@pytest.fixture
def scenario() -> StochasticScenario:
    return StochasticScenario(
        name="s1",
        probability=SCENARIO_PROBABILITY,
        load_profiles={"load1": DEMAND_PROFILE},
    )


@pytest.fixture
def market() -> EnergyMarket:
    return EnergyMarket(name="market1", max_trading_volume_per_step=MAX_TRADING_VOLUME)


# --- validate_loads_consistent_with_scenarios ---


class TestValidateLoadsConsistentWithScenarios:
    def test_valid(self, load: Load, scenario: StochasticScenario) -> None:
        validate_loads_consistent_with_scenarios((load,), (scenario,))

    def test_no_loads_no_profiles(self) -> None:
        scenario = StochasticScenario(name="s1", probability=1.0, load_profiles=None)
        validate_loads_consistent_with_scenarios((), (scenario,))

    def test_loads_but_no_profiles(self, load: Load) -> None:
        scenario = StochasticScenario(name="s1", probability=1.0, load_profiles=None)
        with pytest.raises(OdysValidationError, match="has no load profiles"):
            validate_loads_consistent_with_scenarios((load,), (scenario,))

    def test_missing_load_profile(self, load: Load) -> None:
        scenario = StochasticScenario(name="s1", probability=1.0, load_profiles={})
        with pytest.raises(OdysValidationError, match="is missing load profiles for"):
            validate_loads_consistent_with_scenarios((load,), (scenario,))

    def test_extra_load_profile(self, load: Load) -> None:
        scenario = StochasticScenario(
            name="s1",
            probability=1.0,
            load_profiles={"load1": DEMAND_PROFILE, "extra": DEMAND_PROFILE},
        )
        with pytest.raises(OdysValidationError, match="has load profiles for loads not in portfolio"):
            validate_loads_consistent_with_scenarios((load,), (scenario,))

    def test_no_loads_but_has_profiles(self) -> None:
        scenario = StochasticScenario(name="s1", probability=1.0, load_profiles={"load1": DEMAND_PROFILE})
        with pytest.raises(OdysValidationError, match="Portfolio contains no loads"):
            validate_loads_consistent_with_scenarios((), (scenario,))


# --- validate_markets_consistent_with_scenarios ---


class TestValidateMarketsConsistentWithScenarios:
    def test_valid(self, market: EnergyMarket) -> None:
        scenario = StochasticScenario(
            name="s1",
            probability=1.0,
            market_prices={"market1": MARKET_PRICES},
        )
        validate_markets_consistent_with_scenarios((market,), (scenario,))

    def test_no_markets_no_prices(self) -> None:
        scenario = StochasticScenario(name="s1", probability=1.0, market_prices=None)
        validate_markets_consistent_with_scenarios((), (scenario,))

    def test_markets_but_no_prices(self, market: EnergyMarket) -> None:
        scenario = StochasticScenario(name="s1", probability=1.0, market_prices=None)
        with pytest.raises(OdysValidationError, match="has no market prices"):
            validate_markets_consistent_with_scenarios((market,), (scenario,))

    def test_missing_market_prices(self, market: EnergyMarket) -> None:
        scenario = StochasticScenario(name="s1", probability=1.0, market_prices={})
        with pytest.raises(OdysValidationError, match="is missing market prices for"):
            validate_markets_consistent_with_scenarios((market,), (scenario,))

    def test_extra_market_prices(self, market: EnergyMarket) -> None:
        scenario = StochasticScenario(
            name="s1",
            probability=1.0,
            market_prices={"market1": MARKET_PRICES, "extra": MARKET_PRICES},
        )
        with pytest.raises(OdysValidationError, match="has market prices for markets not in portfolio"):
            validate_markets_consistent_with_scenarios((market,), (scenario,))

    def test_no_markets_but_has_prices(self) -> None:
        scenario = StochasticScenario(name="s1", probability=1.0, market_prices={"m": MARKET_PRICES})
        with pytest.raises(OdysValidationError, match="EnergySystem contains no markets"):
            validate_markets_consistent_with_scenarios((), (scenario,))


# --- validate_load_profiles ---


class TestValidateLoadProfiles:
    def test_valid(self, scenario: StochasticScenario) -> None:
        validate_load_profiles(scenario, NUMBER_OF_STEPS)

    def test_none_profiles(self) -> None:
        scenario = StochasticScenario(name="s1", probability=1.0, load_profiles=None)
        validate_load_profiles(scenario, NUMBER_OF_STEPS)

    def test_length_mismatch(self) -> None:
        scenario = StochasticScenario(name="s1", probability=1.0, load_profiles={"load1": [1.0, 2.0]})
        with pytest.raises(OdysValidationError, match="does not match the number of time steps"):
            validate_load_profiles(scenario, NUMBER_OF_STEPS)


# --- validate_available_capacity_profiles ---


class TestValidateAvailableCapacityProfiles:
    def test_valid(self, portfolio: AssetPortfolio) -> None:
        scenario = StochasticScenario(
            name="s1",
            probability=1.0,
            available_capacity_profiles={"gen1": [90.0, 100.0, 95.0, 100.0]},
        )
        validate_available_capacity_profiles(scenario, portfolio, NUMBER_OF_STEPS)

    def test_none_profiles(self, portfolio: AssetPortfolio) -> None:
        scenario = StochasticScenario(name="s1", probability=1.0, available_capacity_profiles=None)
        validate_available_capacity_profiles(scenario, portfolio, NUMBER_OF_STEPS)

    def test_non_generator_asset(self, portfolio: AssetPortfolio) -> None:
        scenario = StochasticScenario(
            name="s1",
            probability=1.0,
            available_capacity_profiles={"bat1": [25.0, 25.0, 25.0, 25.0]},
        )
        with pytest.raises(OdysValidationError, match="Available capacity can only be specified for generators"):
            validate_available_capacity_profiles(scenario, portfolio, NUMBER_OF_STEPS)

    def test_length_mismatch(self, portfolio: AssetPortfolio) -> None:
        scenario = StochasticScenario(
            name="s1",
            probability=1.0,
            available_capacity_profiles={"gen1": [90.0, 100.0]},
        )
        with pytest.raises(OdysValidationError, match="does not match the number of time steps"):
            validate_available_capacity_profiles(scenario, portfolio, NUMBER_OF_STEPS)

    def test_value_out_of_range(self, portfolio: AssetPortfolio) -> None:
        scenario = StochasticScenario(
            name="s1",
            probability=1.0,
            available_capacity_profiles={"gen1": [90.0, 150.0, 95.0, 100.0]},
        )
        with pytest.raises(OdysValidationError, match=r"Available capacity value.*is invalid"):
            validate_available_capacity_profiles(scenario, portfolio, NUMBER_OF_STEPS)


# --- validate_enough_power_to_meet_demand ---


class TestValidateEnoughPowerToMeetDemand:
    def test_valid(self, generator: Generator, storage: Storage, scenario: StochasticScenario) -> None:
        validate_enough_power_to_meet_demand(scenario, (generator,), (storage,))

    def test_no_load_profiles(self, generator: Generator, storage: Storage) -> None:
        scenario = StochasticScenario(name="s1", probability=1.0, load_profiles=None)
        with pytest.raises(OdysValidationError, match="Load profile is empty"):
            validate_enough_power_to_meet_demand(scenario, (generator,), (storage,))

    def test_demand_exceeds_capacity(self, generator: Generator, storage: Storage) -> None:
        scenario = StochasticScenario(
            name="s1",
            probability=1.0,
            load_profiles={"load1": [80.0, 200.0, 90.0, 100.0]},
        )
        with pytest.raises(OdysValidationError, match="Infeasible problem"):
            validate_enough_power_to_meet_demand(scenario, (generator,), (storage,))


# --- validate_enough_energy_to_meet_demand ---


class TestValidateEnoughEnergyToMeetDemand:
    def test_noop(self, scenario: StochasticScenario) -> None:
        validate_enough_energy_to_meet_demand(scenario)
