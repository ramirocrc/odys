"""Tests for energy system input validation functions."""

from datetime import timedelta

import pytest

from odys.domain.entities.battery import Battery
from odys.domain.entities.charger import Charger
from odys.domain.entities.electric_vehicle import ElectricVehicle
from odys.domain.entities.fixed_load import FixedLoad
from odys.domain.entities.flexible_load import FlexibleLoad
from odys.domain.entities.generator import Generator
from odys.domain.entities.market import EnergyMarket
from odys.domain.entities.portfolio import AssetPortfolio
from odys.domain.entities.stationary_storage import StationaryStorage
from odys.domain.entities.trip import Trip
from odys.domain.exceptions import OdysValidationError
from odys.domain.horizon import Horizon
from odys.domain.profiles import AvailableCapacityProfile, LoadProfile, PriceProfile
from odys.domain.scenario import Scenario, ScenarioSet
from odys.domain.validation import (
    validate_energy_system_inputs,
    validate_enough_energy_to_meet_demand,
    validate_enough_power_to_meet_demand,
    validate_has_load_or_market,
    validate_profile_lengths,
    validate_profiles_reference_system_entities,
    validate_required_profiles_present,
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
HORIZON = Horizon(timestep=timedelta(hours=1), number_of_steps=NUMBER_OF_STEPS)
SCENARIO_PROBABILITY = 1.0
DEMAND_PROFILE = [80.0, 120.0, 90.0, 100.0]
MARKET_PRICES = [10.0, 20.0, 30.0, 40.0]
CAPACITY_PROFILE = [90.0, 100.0, 95.0, 100.0]
MAX_INCREASE = 50.0
MAX_DECREASE = 30.0
VALUE_OF_CONSUMPTION = 100.0
EV_CAPACITY = 50.0
EV_MAX_CHARGE_POWER = 22.0
EV_MAX_DISCHARGE_POWER = 30.0
CHARGER_MAX_POWER = 50.0


@pytest.fixture
def generator() -> Generator:
    return Generator(name="gen1", nominal_power=NOMINAL_POWER, variable_cost=VARIABLE_COST)


@pytest.fixture
def storage() -> StationaryStorage:
    return StationaryStorage(
        name="bat1",
        battery=Battery(
            capacity=STORAGE_CAPACITY,
            max_charge_power=STORAGE_MAX_CHARGE_POWER,
            max_discharge_power=STORAGE_MAX_DISCHARGE_POWER,
            efficiency_charging=STORAGE_EFFICIENCY,
            efficiency_discharging=STORAGE_EFFICIENCY,
            soc_start=SOC_START,
        ),
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
def portfolio(generator: Generator, storage: StationaryStorage, load: FixedLoad) -> AssetPortfolio:
    return AssetPortfolio(assets=[generator, storage, load])


@pytest.fixture
def scenario(load: FixedLoad) -> Scenario:
    return Scenario(
        name="s1",
        probability=SCENARIO_PROBABILITY,
        profiles=(LoadProfile(load=load, values=DEMAND_PROFILE),),
    )


@pytest.fixture
def market() -> EnergyMarket:
    return EnergyMarket(name="market1", max_trading_volume_per_step=MAX_TRADING_VOLUME)


def _electric_vehicle(trips: tuple[Trip, ...] = ()) -> ElectricVehicle:
    return ElectricVehicle(
        name="ev1",
        battery=Battery(
            capacity=EV_CAPACITY,
            max_charge_power=EV_MAX_CHARGE_POWER,
            max_discharge_power=EV_MAX_DISCHARGE_POWER,
            soc_start=SOC_START,
        ),
        trips=trips,
    )


class TestValidateEnergySystemInputs:
    def test_valid(self, portfolio: AssetPortfolio, scenario: Scenario) -> None:
        validate_energy_system_inputs(portfolio, ScenarioSet(scenarios=(scenario,)), (), HORIZON)

    def test_checks_every_entity_against_the_horizon(self, generator: Generator, load: FixedLoad) -> None:
        late_trip = Trip(name="late_trip", start_time=2, end_time=NUMBER_OF_STEPS + 1, energy_consumption=5.0)
        portfolio = AssetPortfolio([
            generator,
            load,
            _electric_vehicle((late_trip,)),
            Charger(name="charger1", max_power=CHARGER_MAX_POWER),
        ])
        scenario = Scenario(profiles=(LoadProfile(load=load, values=DEMAND_PROFILE),))
        with pytest.raises(OdysValidationError, match="Trip 'late_trip' for vehicle 'ev1' extends beyond"):
            validate_energy_system_inputs(portfolio, ScenarioSet(scenarios=(scenario,)), (), HORIZON)

    def test_energy_check_is_skipped_with_markets(self, storage: StationaryStorage, load: FixedLoad) -> None:
        small_volume = 1.0
        market = EnergyMarket(name="market1", max_trading_volume_per_step=small_volume)
        scenario = Scenario(
            profiles=(
                LoadProfile(load=load, values=[20.0] * NUMBER_OF_STEPS),
                PriceProfile(market=market, values=MARKET_PRICES),
            ),
        )
        validate_energy_system_inputs(
            AssetPortfolio([storage, load]),
            ScenarioSet(scenarios=(scenario,)),
            (market,),
            HORIZON,
        )


class TestValidateProfilesReferenceSystemEntities:
    def test_profiles_referencing_system_entities_are_valid(
        self,
        portfolio: AssetPortfolio,
        generator: Generator,
        market: EnergyMarket,
        scenario: Scenario,
    ) -> None:
        capacity_and_price = Scenario(
            name="s2",
            probability=0.0,
            profiles=(
                AvailableCapacityProfile(generator=generator, values=CAPACITY_PROFILE),
                PriceProfile(market=market, values=MARKET_PRICES),
            ),
        )
        validate_profiles_reference_system_entities((scenario, capacity_and_price), portfolio, (market,))

    def test_market_and_asset_sharing_a_name_are_both_matched(
        self,
        portfolio: AssetPortfolio,
        generator: Generator,
        market: EnergyMarket,
    ) -> None:
        market_named_like_generator = market.model_copy(update={"name": generator.name})
        scenario = Scenario(
            profiles=(
                AvailableCapacityProfile(generator=generator, values=CAPACITY_PROFILE),
                PriceProfile(market=market_named_like_generator, values=MARKET_PRICES),
            ),
        )
        validate_profiles_reference_system_entities((scenario,), portfolio, (market_named_like_generator,))

    def test_rejects_fixed_load_profile_for_a_load_not_in_the_portfolio(
        self,
        portfolio: AssetPortfolio,
        load: FixedLoad,
    ) -> None:
        extra_load = load.model_copy(update={"name": "extra"})
        scenario = Scenario(
            name="s1",
            profiles=(
                LoadProfile(load=load, values=DEMAND_PROFILE),
                LoadProfile(load=extra_load, values=DEMAND_PROFILE),
            ),
        )
        with pytest.raises(
            OdysValidationError,
            match="Scenario 's1' has a LoadProfile for 'extra', which is not in the energy system",
        ):
            validate_profiles_reference_system_entities((scenario,), portfolio, ())

    def test_rejects_flexible_load_profile_when_the_portfolio_has_no_flexible_loads(
        self,
        portfolio: AssetPortfolio,
        flexible_load: FlexibleLoad,
    ) -> None:
        scenario = Scenario(name="s1", profiles=(LoadProfile(load=flexible_load, values=DEMAND_PROFILE),))
        with pytest.raises(
            OdysValidationError,
            match="Scenario 's1' has a LoadProfile for 'flex_load1', which is not in the energy system",
        ):
            validate_profiles_reference_system_entities((scenario,), portfolio, ())

    def test_rejects_price_for_a_market_not_in_the_system(
        self,
        portfolio: AssetPortfolio,
        market: EnergyMarket,
    ) -> None:
        extra_market = market.model_copy(update={"name": "extra"})
        scenario = Scenario(
            name="s1",
            profiles=(
                PriceProfile(market=market, values=MARKET_PRICES),
                PriceProfile(market=extra_market, values=MARKET_PRICES),
            ),
        )
        with pytest.raises(
            OdysValidationError,
            match="Scenario 's1' has a PriceProfile for 'extra', which is not in the energy system",
        ):
            validate_profiles_reference_system_entities((scenario,), portfolio, (market,))

    def test_rejects_price_when_the_system_has_no_markets(
        self,
        portfolio: AssetPortfolio,
        market: EnergyMarket,
    ) -> None:
        scenario = Scenario(name="s1", profiles=(PriceProfile(market=market, values=MARKET_PRICES),))
        with pytest.raises(
            OdysValidationError,
            match="Scenario 's1' has a PriceProfile for 'market1', which is not in the energy system",
        ):
            validate_profiles_reference_system_entities((scenario,), portfolio, ())

    def test_rejects_asset_profile_for_a_different_asset_with_the_same_name(
        self,
        portfolio: AssetPortfolio,
        generator: Generator,
    ) -> None:
        stale_generator = generator.model_copy(update={"nominal_power": NOMINAL_POWER / 2})
        scenario = Scenario(
            name="s1",
            profiles=(AvailableCapacityProfile(generator=stale_generator, values=[50.0] * 4),),
        )
        with pytest.raises(
            OdysValidationError,
            match="Scenario 's1': the AvailableCapacityProfile for 'gen1' does not reference the entity",
        ):
            validate_profiles_reference_system_entities((scenario,), portfolio, ())

    def test_rejects_capacity_for_a_generator_named_like_a_non_generator_asset(
        self,
        portfolio: AssetPortfolio,
        generator: Generator,
        storage: StationaryStorage,
    ) -> None:
        impostor = generator.model_copy(update={"name": storage.name})
        scenario = Scenario(
            name="s1",
            profiles=(AvailableCapacityProfile(generator=impostor, values=[25.0, 25.0, 25.0, 25.0]),),
        )
        with pytest.raises(
            OdysValidationError,
            match="Scenario 's1': the AvailableCapacityProfile for 'bat1' does not reference the entity",
        ):
            validate_profiles_reference_system_entities((scenario,), portfolio, ())

    def test_rejects_price_for_a_different_market_with_the_same_name(
        self,
        portfolio: AssetPortfolio,
        market: EnergyMarket,
    ) -> None:
        stale_market = market.model_copy(update={"max_trading_volume_per_step": MAX_TRADING_VOLUME / 2})
        scenario = Scenario(name="s1", profiles=(PriceProfile(market=stale_market, values=MARKET_PRICES),))
        with pytest.raises(OdysValidationError, match="the PriceProfile for 'market1' does not reference the entity"):
            validate_profiles_reference_system_entities((scenario,), portfolio, (market,))


class TestValidateRequiredProfilesPresent:
    def test_valid(self, generator: Generator, load: FixedLoad, market: EnergyMarket) -> None:
        scenario = Scenario(
            profiles=(
                LoadProfile(load=load, values=DEMAND_PROFILE),
                PriceProfile(market=market, values=MARKET_PRICES),
            ),
        )
        validate_required_profiles_present((scenario,), (generator, load, market))

    def test_no_entities_need_no_profiles(self) -> None:
        validate_required_profiles_present((Scenario(),), ())

    def test_generator_capacity_profile_is_optional(self, generator: Generator) -> None:
        validate_required_profiles_present((Scenario(),), (generator,))

    def test_missing_fixed_load_profile(self, load: FixedLoad) -> None:
        other_load = load.model_copy(update={"name": "load2"})
        scenario = Scenario(name="s1", profiles=(LoadProfile(load=load, values=DEMAND_PROFILE),))
        with pytest.raises(OdysValidationError, match=r"Scenario 's1' is missing a LoadProfile for: \['load2'\]"):
            validate_required_profiles_present((scenario,), (load, other_load))

    def test_loads_but_no_profiles(self, load: FixedLoad) -> None:
        with pytest.raises(OdysValidationError, match=r"Scenario 's1' is missing a LoadProfile for: \['load1'\]"):
            validate_required_profiles_present((Scenario(name="s1"),), (load,))

    def test_missing_flexible_load_profile(self, flexible_load: FlexibleLoad) -> None:
        other_load = flexible_load.model_copy(update={"name": "flex_load2"})
        scenario = Scenario(name="s1", profiles=(LoadProfile(load=flexible_load, values=DEMAND_PROFILE),))
        with pytest.raises(OdysValidationError, match=r"is missing a LoadProfile for: \['flex_load2'\]"):
            validate_required_profiles_present((scenario,), (flexible_load, other_load))

    def test_missing_market_prices(self, market: EnergyMarket) -> None:
        other_market = market.model_copy(update={"name": "market2"})
        scenario = Scenario(name="s1", profiles=(PriceProfile(market=market, values=MARKET_PRICES),))
        with pytest.raises(OdysValidationError, match=r"is missing a PriceProfile for: \['market2'\]"):
            validate_required_profiles_present((scenario,), (market, other_market))

    def test_every_scenario_is_checked(self, load: FixedLoad) -> None:
        complete = Scenario(name="s1", probability=0.5, profiles=(LoadProfile(load=load, values=DEMAND_PROFILE),))
        incomplete = Scenario(name="s2", probability=0.5)
        with pytest.raises(OdysValidationError, match=r"Scenario 's2' is missing a LoadProfile for: \['load1'\]"):
            validate_required_profiles_present((complete, incomplete), (load,))


class TestValidateProfileLengths:
    def test_valid(self, scenario: Scenario) -> None:
        validate_profile_lengths((scenario,), HORIZON)

    def test_no_profiles(self) -> None:
        validate_profile_lengths((Scenario(),), HORIZON)

    def test_fixed_load_length_mismatch(self, load: FixedLoad) -> None:
        scenario = Scenario(name="s1", profiles=(LoadProfile(load=load, values=[1.0, 2.0]),))
        with pytest.raises(
            OdysValidationError,
            match="Scenario 's1': the LoadProfile for 'load1' has 2 values, but the horizon has 4 steps",
        ):
            validate_profile_lengths((scenario,), HORIZON)

    def test_flexible_load_length_mismatch(self, flexible_load: FlexibleLoad) -> None:
        scenario = Scenario(name="s1", profiles=(LoadProfile(load=flexible_load, values=[40.0, 50.0]),))
        with pytest.raises(OdysValidationError, match="the LoadProfile for 'flex_load1' has 2 values"):
            validate_profile_lengths((scenario,), HORIZON)

    def test_capacity_length_mismatch(self, generator: Generator) -> None:
        scenario = Scenario(name="s1", profiles=(AvailableCapacityProfile(generator=generator, values=[90.0, 100.0]),))
        with pytest.raises(OdysValidationError, match="the AvailableCapacityProfile for 'gen1' has 2 values"):
            validate_profile_lengths((scenario,), HORIZON)

    def test_price_length_mismatch(self, market: EnergyMarket) -> None:
        scenario = Scenario(name="s1", profiles=(PriceProfile(market=market, values=[10.0, 20.0, 30.0]),))
        with pytest.raises(OdysValidationError, match="the PriceProfile for 'market1' has 3 values"):
            validate_profile_lengths((scenario,), HORIZON)


class TestValidateHasLoadOrMarket:
    def test_load_without_market_is_valid(self, scenario: Scenario) -> None:
        validate_has_load_or_market(scenario, ())

    def test_market_only_no_loads_is_valid(self, market: EnergyMarket) -> None:
        validate_has_load_or_market(Scenario(), (market,))

    def test_no_load_and_no_market(self) -> None:
        with pytest.raises(OdysValidationError, match="Load profile is empty, there is nothing to balance"):
            validate_has_load_or_market(Scenario(), ())


class TestValidateEnoughPowerToMeetDemand:
    def test_valid(self, generator: Generator, storage: StationaryStorage, load: FixedLoad, scenario: Scenario) -> None:
        validate_enough_power_to_meet_demand(scenario, (generator, storage, load), HORIZON)

    def test_market_only_no_loads_is_valid(
        self,
        generator: Generator,
        storage: StationaryStorage,
        market: EnergyMarket,
    ) -> None:
        scenario = Scenario(profiles=(PriceProfile(market=market, values=MARKET_PRICES),))
        validate_enough_power_to_meet_demand(scenario, (generator, storage, market), HORIZON)

    def test_demand_exceeds_capacity(self, generator: Generator, storage: StationaryStorage, load: FixedLoad) -> None:
        scenario = Scenario(name="s1", profiles=(LoadProfile(load=load, values=[80.0, 200.0, 90.0, 100.0]),))
        with pytest.raises(
            OdysValidationError,
            match=r"Infeasible problem in scenario 's1' at time index 1: minimum demand = 200.0.* = 125.0",
        ):
            validate_enough_power_to_meet_demand(scenario, (generator, storage, load), HORIZON)

    def test_demand_is_summed_over_loads(
        self,
        generator: Generator,
        storage: StationaryStorage,
        load: FixedLoad,
    ) -> None:
        other_load = load.model_copy(update={"name": "load2"})
        within_supply_alone = [100.0, 100.0, 100.0, 100.0]
        scenario = Scenario(
            name="s1",
            profiles=(
                LoadProfile(load=load, values=within_supply_alone),
                LoadProfile(load=other_load, values=within_supply_alone),
            ),
        )
        with pytest.raises(OdysValidationError, match=r"time index 0: minimum demand = 200\.0"):
            validate_enough_power_to_meet_demand(scenario, (generator, storage, load, other_load), HORIZON)

    def test_flexible_load_feasible_after_decrease(
        self,
        generator: Generator,
        storage: StationaryStorage,
        flexible_load: FlexibleLoad,
    ) -> None:
        scenario = Scenario(profiles=(LoadProfile(load=flexible_load, values=[80.0, 150.0, 90.0, 100.0]),))
        validate_enough_power_to_meet_demand(scenario, (generator, storage, flexible_load), HORIZON)

    def test_flexible_load_feasible_with_decrease_at_the_limit(
        self,
        generator: Generator,
        storage: StationaryStorage,
        flexible_load: FlexibleLoad,
    ) -> None:
        scenario = Scenario(profiles=(LoadProfile(load=flexible_load, values=[80.0, 155.0, 90.0, 100.0]),))
        validate_enough_power_to_meet_demand(scenario, (generator, storage, flexible_load), HORIZON)

    def test_flexible_load_infeasible_even_with_decrease(
        self,
        generator: Generator,
        storage: StationaryStorage,
        flexible_load: FlexibleLoad,
    ) -> None:
        scenario = Scenario(profiles=(LoadProfile(load=flexible_load, values=[80.0, 200.0, 90.0, 100.0]),))
        with pytest.raises(OdysValidationError, match=r"time index 1: minimum demand = 170\.0"):
            validate_enough_power_to_meet_demand(scenario, (generator, storage, flexible_load), HORIZON)

    def test_market_volume_counted_toward_available_power(
        self,
        generator: Generator,
        storage: StationaryStorage,
        market: EnergyMarket,
        load: FixedLoad,
    ) -> None:
        scenario = Scenario(profiles=(LoadProfile(load=load, values=[80.0, 200.0, 90.0, 100.0]),))
        validate_enough_power_to_meet_demand(scenario, (generator, storage, market, load), HORIZON)

    def test_infeasible_even_with_market(
        self,
        generator: Generator,
        storage: StationaryStorage,
        market: EnergyMarket,
        load: FixedLoad,
    ) -> None:
        scenario = Scenario(profiles=(LoadProfile(load=load, values=[80.0, 300.0, 90.0, 100.0]),))
        with pytest.raises(OdysValidationError, match="Infeasible problem"):
            validate_enough_power_to_meet_demand(scenario, (generator, storage, market, load), HORIZON)

    def test_uses_available_capacity_profile_per_timestep(
        self,
        generator: Generator,
        storage: StationaryStorage,
        load: FixedLoad,
    ) -> None:
        scenario = Scenario(
            profiles=(
                AvailableCapacityProfile(generator=generator, values=[100.0, 50.0, 100.0, 100.0]),
                LoadProfile(load=load, values=[70.0, 80.0, 70.0, 70.0]),
            ),
        )
        with pytest.raises(OdysValidationError, match="time index 1"):
            validate_enough_power_to_meet_demand(scenario, (generator, storage, load), HORIZON)

    def test_electric_vehicle_discharge_counts_as_supply(self, generator: Generator, load: FixedLoad) -> None:
        above_generator_alone = [120.0, 120.0, 120.0, 120.0]
        scenario = Scenario(profiles=(LoadProfile(load=load, values=above_generator_alone),))
        with pytest.raises(OdysValidationError, match="Infeasible problem"):
            validate_enough_power_to_meet_demand(scenario, (generator, load), HORIZON)

        validate_enough_power_to_meet_demand(scenario, (generator, load, _electric_vehicle()), HORIZON)


class TestValidateEnoughEnergyToMeetDemand:
    def test_no_loads(self, generator: Generator, storage: StationaryStorage) -> None:
        validate_enough_energy_to_meet_demand(Scenario(), (generator, storage), HORIZON)

    def test_valid(self, generator: Generator, storage: StationaryStorage, load: FixedLoad, scenario: Scenario) -> None:
        validate_enough_energy_to_meet_demand(scenario, (generator, storage, load), HORIZON)

    def test_infeasible_energy_but_feasible_power(self, storage: StationaryStorage, load: FixedLoad) -> None:
        scenario = Scenario(name="s1", profiles=(LoadProfile(load=load, values=[20.0, 20.0, 20.0, 20.0]),))
        validate_enough_power_to_meet_demand(scenario, (storage, load), HORIZON)

        with pytest.raises(
            OdysValidationError,
            match=r"Infeasible problem in scenario 's1': total energy demand \(80.0\).*available energy \(50.0\)",
        ):
            validate_enough_energy_to_meet_demand(scenario, (storage, load), HORIZON)

    def test_uses_available_capacity_profile_not_nominal_power(self, generator: Generator, load: FixedLoad) -> None:
        scenario = Scenario(
            profiles=(
                AvailableCapacityProfile(generator=generator, values=[20.0, 20.0, 20.0, 20.0]),
                LoadProfile(load=load, values=[25.0, 25.0, 25.0, 25.0]),
            ),
        )
        with pytest.raises(OdysValidationError, match="Infeasible problem"):
            validate_enough_energy_to_meet_demand(scenario, (generator, load), HORIZON)

    def test_market_energy_included(self, load: FixedLoad, market: EnergyMarket) -> None:
        scenario = Scenario(profiles=(LoadProfile(load=load, values=[25.0, 25.0, 25.0, 25.0]),))
        with pytest.raises(OdysValidationError, match="Infeasible problem"):
            validate_enough_energy_to_meet_demand(scenario, (load,), HORIZON)

        validate_enough_energy_to_meet_demand(scenario, (load, market), HORIZON)

    def test_flexible_load_min_possible_demand_used(self, flexible_load: FlexibleLoad) -> None:
        scenario = Scenario(profiles=(LoadProfile(load=flexible_load, values=[40.0, 40.0, 40.0, 40.0]),))
        with pytest.raises(OdysValidationError, match=r"total energy demand \(40.0\)"):
            validate_enough_energy_to_meet_demand(scenario, (flexible_load,), HORIZON)

    def test_energy_scales_with_timestep(self, generator: Generator, load: FixedLoad) -> None:
        half_hour = Horizon(timestep=timedelta(minutes=30), number_of_steps=NUMBER_OF_STEPS)
        scenario = Scenario(
            profiles=(
                AvailableCapacityProfile(generator=generator, values=[20.0, 20.0, 20.0, 20.0]),
                LoadProfile(load=load, values=[25.0, 25.0, 25.0, 25.0]),
            ),
        )
        with pytest.raises(OdysValidationError, match=r"total energy demand \(50.0\).*available energy \(40.0\)"):
            validate_enough_energy_to_meet_demand(scenario, (generator, load), half_hour)
