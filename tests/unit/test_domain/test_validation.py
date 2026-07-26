"""Tests for energy system input validation functions."""

import pytest

from odys.domain.entities.charger import Charger
from odys.domain.entities.electric_vehicle import ElectricVehicle
from odys.domain.entities.fixed_load import FixedLoad
from odys.domain.entities.flexible_load import FlexibleLoad
from odys.domain.entities.generator import Generator
from odys.domain.entities.market import EnergyMarket
from odys.domain.entities.portfolio import AssetPortfolio
from odys.domain.entities.standalone_storage import StandaloneStorage
from odys.domain.entities.trip import Trip
from odys.domain.exceptions import OdysValidationError
from odys.domain.scenarios import StochasticScenario
from odys.domain.validation import (
    validate_available_capacity_profiles,
    validate_chargers_and_evs_consistency,
    validate_electric_vehicle_trips,
    validate_enough_energy_to_meet_demand,
    validate_enough_power_to_meet_demand,
    validate_fixed_loads_consistent_with_scenarios,
    validate_flexible_loads_consistent_with_scenarios,
    validate_load_profiles,
    validate_markets_consistent_with_scenarios,
)

NOMINAL_POWER = 100.0
VARIABLE_COST = 50.0
STORAGE_CAPACITY = 50.0
STORAGE_MAX_CHARGE_POWER = 25.0
STORAGE_MAX_DISCHARGE_POWER = 25.0
STORAGE_EFFICIENCY = 0.9
SOC_START = 0.5
MAX_TRADING_VOLUME = 100.0
NUMBER_OF_STEPS = 4
SCENARIO_PROBABILITY = 1.0
DEMAND_PROFILE = [80.0, 120.0, 90.0, 100.0]
MARKET_PRICES = [10.0, 20.0, 30.0, 40.0]
MAX_INCREASE = 50.0
MAX_DECREASE = 30.0
VALUE_OF_CONSUMPTION = 100.0


@pytest.fixture
def generator() -> Generator:
    return Generator(name="gen1", nominal_power=NOMINAL_POWER, variable_cost=VARIABLE_COST)


@pytest.fixture
def storage() -> StandaloneStorage:
    return StandaloneStorage(
        name="bat1",
        capacity=STORAGE_CAPACITY,
        max_charge_power=STORAGE_MAX_CHARGE_POWER,
        max_discharge_power=STORAGE_MAX_DISCHARGE_POWER,
        efficiency_charging=STORAGE_EFFICIENCY,
        efficiency_discharging=STORAGE_EFFICIENCY,
        soc_start=SOC_START,
    )


@pytest.fixture
def load() -> FixedLoad:
    return FixedLoad(name="load1")


@pytest.fixture
def flexible_load() -> FlexibleLoad:
    return FlexibleLoad(
        name="flex_load1",
        max_increase=MAX_INCREASE,
        max_decrease=MAX_DECREASE,
        value_of_consumption=VALUE_OF_CONSUMPTION,
    )


@pytest.fixture
def portfolio(generator: Generator, storage: StandaloneStorage, load: FixedLoad) -> AssetPortfolio:
    return AssetPortfolio(assets=[generator, storage, load])


@pytest.fixture
def scenario() -> StochasticScenario:
    return StochasticScenario(
        name="s1",
        probability=SCENARIO_PROBABILITY,
        fixed_load_profiles={"load1": DEMAND_PROFILE},
    )


@pytest.fixture
def market() -> EnergyMarket:
    return EnergyMarket(name="market1", max_trading_volume_per_step=MAX_TRADING_VOLUME)


# --- validate_fixed_loads_consistent_with_scenarios ---


class TestValidateLoadsConsistentWithScenarios:
    def test_valid(self, load: FixedLoad, scenario: StochasticScenario) -> None:
        validate_fixed_loads_consistent_with_scenarios((load,), (scenario,))

    def test_no_loads_no_profiles(self) -> None:
        scenario = StochasticScenario(name="s1", probability=1.0, fixed_load_profiles=None)
        validate_fixed_loads_consistent_with_scenarios((), (scenario,))

    def test_loads_but_no_profiles(self, load: FixedLoad) -> None:
        scenario = StochasticScenario(name="s1", probability=1.0, fixed_load_profiles=None)
        with pytest.raises(OdysValidationError, match="has no fixed load profiles"):
            validate_fixed_loads_consistent_with_scenarios((load,), (scenario,))

    def test_missing_load_profile(self, load: FixedLoad) -> None:
        scenario = StochasticScenario(name="s1", probability=1.0, fixed_load_profiles={})
        with pytest.raises(OdysValidationError, match="is missing fixed load profiles for"):
            validate_fixed_loads_consistent_with_scenarios((load,), (scenario,))

    def test_extra_load_profile(self, load: FixedLoad) -> None:
        scenario = StochasticScenario(
            name="s1",
            probability=1.0,
            fixed_load_profiles={"load1": DEMAND_PROFILE, "extra": DEMAND_PROFILE},
        )
        with pytest.raises(OdysValidationError, match="has fixed load profiles for loads not in portfolio"):
            validate_fixed_loads_consistent_with_scenarios((load,), (scenario,))

    def test_no_loads_but_has_profiles(self) -> None:
        scenario = StochasticScenario(name="s1", probability=1.0, fixed_load_profiles={"load1": DEMAND_PROFILE})
        with pytest.raises(OdysValidationError, match="Portfolio contains no fixed loads"):
            validate_fixed_loads_consistent_with_scenarios((), (scenario,))


# --- validate_flexible_loads_consistent_with_scenarios ---


class TestValidateFlexibleLoadsConsistentWithScenarios:
    def test_valid(self, flexible_load: FlexibleLoad) -> None:
        scenario = StochasticScenario(
            name="s1",
            probability=1.0,
            flexible_load_base_profiles={"flex_load1": DEMAND_PROFILE},
        )
        validate_flexible_loads_consistent_with_scenarios((flexible_load,), (scenario,))

    def test_no_loads_no_profiles(self) -> None:
        scenario = StochasticScenario(name="s1", probability=1.0, flexible_load_base_profiles=None)
        validate_flexible_loads_consistent_with_scenarios((), (scenario,))

    def test_loads_but_no_profiles(self, flexible_load: FlexibleLoad) -> None:
        scenario = StochasticScenario(name="s1", probability=1.0, flexible_load_base_profiles=None)
        with pytest.raises(OdysValidationError, match="has no flexible load base profiles"):
            validate_flexible_loads_consistent_with_scenarios((flexible_load,), (scenario,))

    def test_missing_load_profile(self, flexible_load: FlexibleLoad) -> None:
        scenario = StochasticScenario(name="s1", probability=1.0, flexible_load_base_profiles={})
        with pytest.raises(OdysValidationError, match="is missing flexible load base profiles for"):
            validate_flexible_loads_consistent_with_scenarios((flexible_load,), (scenario,))

    def test_extra_load_profile(self, flexible_load: FlexibleLoad) -> None:
        scenario = StochasticScenario(
            name="s1",
            probability=1.0,
            flexible_load_base_profiles={"flex_load1": DEMAND_PROFILE, "extra": DEMAND_PROFILE},
        )
        with pytest.raises(OdysValidationError, match="has flexible load base profiles for loads not in portfolio"):
            validate_flexible_loads_consistent_with_scenarios((flexible_load,), (scenario,))

    def test_no_loads_but_has_profiles(self) -> None:
        scenario = StochasticScenario(
            name="s1",
            probability=1.0,
            flexible_load_base_profiles={"flex_load1": DEMAND_PROFILE},
        )
        with pytest.raises(OdysValidationError, match="Portfolio contains no flexible loads"):
            validate_flexible_loads_consistent_with_scenarios((), (scenario,))


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
        scenario = StochasticScenario(name="s1", probability=1.0, fixed_load_profiles=None)
        validate_load_profiles(scenario, NUMBER_OF_STEPS)

    def test_length_mismatch(self) -> None:
        scenario = StochasticScenario(name="s1", probability=1.0, fixed_load_profiles={"load1": [1.0, 2.0]})
        with pytest.raises(OdysValidationError, match="does not match the number of time steps"):
            validate_load_profiles(scenario, NUMBER_OF_STEPS)

    def test_flexible_load_length_mismatch(self) -> None:
        scenario = StochasticScenario(
            name="s1",
            probability=1.0,
            flexible_load_base_profiles={"flex_load1": [1.0, 2.0]},
        )
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
    def test_valid(self, generator: Generator, storage: StandaloneStorage, scenario: StochasticScenario) -> None:
        validate_enough_power_to_meet_demand(scenario, (generator,), (storage,))

    def test_no_load_profiles(self, generator: Generator, storage: StandaloneStorage) -> None:
        scenario = StochasticScenario(name="s1", probability=1.0, fixed_load_profiles=None)
        with pytest.raises(OdysValidationError, match="Load profile is empty"):
            validate_enough_power_to_meet_demand(scenario, (generator,), (storage,))

    def test_demand_exceeds_capacity(self, generator: Generator, storage: StandaloneStorage) -> None:
        scenario = StochasticScenario(
            name="s1",
            probability=1.0,
            fixed_load_profiles={"load1": [80.0, 200.0, 90.0, 100.0]},
        )
        with pytest.raises(OdysValidationError, match="Infeasible problem"):
            validate_enough_power_to_meet_demand(scenario, (generator,), (storage,))

    def test_flexible_load_feasible_after_decrease(
        self,
        generator: Generator,
        storage: StandaloneStorage,
        flexible_load: FlexibleLoad,
    ) -> None:
        # Base demand (150) > capacity (125), but base - max_decrease (150 - 30 = 120) < capacity
        # This should pass
        scenario = StochasticScenario(
            name="s1",
            probability=1.0,
            flexible_load_base_profiles={"flex_load1": [80.0, 150.0, 90.0, 100.0]},
        )
        validate_enough_power_to_meet_demand(scenario, (generator,), (storage,), (flexible_load,))

    def test_flexible_load_infeasible_even_with_decrease(
        self,
        generator: Generator,
        storage: StandaloneStorage,
        flexible_load: FlexibleLoad,
    ) -> None:
        # Base demand (200) - max_decrease (30) = 170 > capacity (150)
        scenario = StochasticScenario(
            name="s1",
            probability=1.0,
            flexible_load_base_profiles={"flex_load1": [80.0, 200.0, 90.0, 100.0]},
        )
        with pytest.raises(OdysValidationError, match="Infeasible problem"):
            validate_enough_power_to_meet_demand(scenario, (generator,), (storage,), (flexible_load,))

    def test_flexible_load_feasible_with_decrease(
        self,
        generator: Generator,
        storage: StandaloneStorage,
        flexible_load: FlexibleLoad,
    ) -> None:
        # Base demand (170) > capacity (150), but base - max_decrease (170 - 30 = 140) < capacity
        # This should pass
        scenario = StochasticScenario(
            name="s1",
            probability=1.0,
            flexible_load_base_profiles={"flex_load1": [80.0, 170.0, 90.0, 100.0]},
        )
        validate_enough_power_to_meet_demand(scenario, (generator,), (storage,), (flexible_load,))


# --- validate_enough_energy_to_meet_demand ---


class TestValidateEnoughEnergyToMeetDemand:
    def test_noop(self, scenario: StochasticScenario) -> None:
        validate_enough_energy_to_meet_demand(scenario)


# --- validate_electric_vehicle_trips ---


EV_CAPACITY = 50.0
EV_MAX_CHARGE_POWER = 22.0
EV_SOC_START = 0.8
TRIP_ENERGY = 5.0
EV_NUMBER_OF_STEPS = 24


class TestValidateElectricVehicleTrips:
    def test_valid(self) -> None:
        trip1 = Trip(name="morning", start_time=8, end_time=10, energy_consumption=TRIP_ENERGY)
        trip2 = Trip(name="evening", start_time=17, end_time=19, energy_consumption=TRIP_ENERGY)
        ev = ElectricVehicle(
            name="ev1",
            capacity=EV_CAPACITY,
            max_charge_power=EV_MAX_CHARGE_POWER,
            max_discharge_power=0.0,
            soc_start=EV_SOC_START,
            trips=(trip1, trip2),
        )
        portfolio = AssetPortfolio(assets=[ev])
        validate_electric_vehicle_trips(portfolio, EV_NUMBER_OF_STEPS)

    def test_no_evs_no_profiles(self) -> None:
        portfolio = AssetPortfolio()
        validate_electric_vehicle_trips(portfolio, EV_NUMBER_OF_STEPS)

    def test_overlapping_trips(self) -> None:
        trip1 = Trip(name="morning", start_time=8, end_time=10, energy_consumption=TRIP_ENERGY)
        trip2 = Trip(name="overlapping", start_time=9, end_time=11, energy_consumption=TRIP_ENERGY)
        ev = ElectricVehicle(
            name="ev1",
            capacity=EV_CAPACITY,
            max_charge_power=EV_MAX_CHARGE_POWER,
            max_discharge_power=0.0,
            soc_start=EV_SOC_START,
            trips=(trip1, trip2),
        )
        portfolio = AssetPortfolio(assets=[ev])
        with pytest.raises(OdysValidationError, match="overlap"):
            validate_electric_vehicle_trips(portfolio, EV_NUMBER_OF_STEPS)

    def test_trips_beyond_horizon(self) -> None:
        trip1 = Trip(name="late_trip", start_time=20, end_time=30, energy_consumption=TRIP_ENERGY)
        ev = ElectricVehicle(
            name="ev1",
            capacity=EV_CAPACITY,
            max_charge_power=EV_MAX_CHARGE_POWER,
            max_discharge_power=0.0,
            soc_start=EV_SOC_START,
            trips=(trip1,),
        )
        portfolio = AssetPortfolio(assets=[ev])
        with pytest.raises(OdysValidationError, match="beyond"):
            validate_electric_vehicle_trips(portfolio, EV_NUMBER_OF_STEPS)


# --- validate_chargers_and_evs_consistency ---


CHARGER_MAX_POWER = 50.0


def _make_ev() -> ElectricVehicle:
    return ElectricVehicle(
        name="ev1",
        capacity=EV_CAPACITY,
        max_charge_power=EV_MAX_CHARGE_POWER,
        max_discharge_power=0.0,
        soc_start=EV_SOC_START,
        trips=(),
    )


class TestValidateChargersAndEvsConsistency:
    def test_both_present(self) -> None:
        portfolio = AssetPortfolio(assets=[_make_ev(), Charger(name="charger1", max_power=CHARGER_MAX_POWER)])
        validate_chargers_and_evs_consistency(portfolio)

    def test_both_absent(self) -> None:
        portfolio = AssetPortfolio()
        validate_chargers_and_evs_consistency(portfolio)

    def test_evs_without_chargers(self) -> None:
        portfolio = AssetPortfolio(assets=[_make_ev()])
        with pytest.raises(OdysValidationError, match="both chargers and electric vehicles"):
            validate_chargers_and_evs_consistency(portfolio)

    def test_chargers_without_evs(self) -> None:
        portfolio = AssetPortfolio(assets=[Charger(name="charger1", max_power=CHARGER_MAX_POWER)])
        with pytest.raises(OdysValidationError, match="both chargers and electric vehicles"):
            validate_chargers_and_evs_consistency(portfolio)
