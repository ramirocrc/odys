"""Tests for energy system input validation functions."""

from datetime import timedelta

import pytest

from odys.domain.conditions import (
    ConditionSet,
    ElectricVehicleInitialState,
    GeneratorFinalState,
    GeneratorInitialState,
    StorageInitialState,
)
from odys.domain.entities.battery import Battery
from odys.domain.entities.battery_storage import BatteryStorage
from odys.domain.entities.charger import Charger
from odys.domain.entities.electric_vehicle import ElectricVehicle
from odys.domain.entities.fixed_load import FixedLoad
from odys.domain.entities.flexible_load import FlexibleLoad
from odys.domain.entities.generator import Generator
from odys.domain.entities.market import EnergyMarket
from odys.domain.entities.portfolio import AssetPortfolio
from odys.domain.entities.trip import Trip
from odys.domain.exceptions import OdysValidationError
from odys.domain.horizon import Horizon
from odys.domain.profiles import AvailableCapacityProfile, FlexibleLoadProfile, LoadProfile, PriceProfile
from odys.domain.scenario import Scenario, ScenarioSet
from odys.domain.validation import (
    validate_conditions_fit_the_run,
    validate_conditions_reference_system_assets,
    validate_energy_system_inputs,
    validate_enough_energy_to_meet_demand,
    validate_enough_power_to_meet_demand,
    validate_has_load_or_market,
    validate_profile_lengths,
    validate_profiles_reference_system_entities,
    validate_required_initial_conditions_present,
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
FLEXIBLE_RANGE_WIDTH = 50.0
VALUE_OF_CONSUMPTION = 100.0
EV_CAPACITY = 50.0
EV_MAX_CHARGE_POWER = 22.0
EV_MAX_DISCHARGE_POWER = 30.0
CHARGER_MAX_POWER = 50.0
RAMP_UP = 40.0
INITIAL_POWER = 50.0
FINAL_POWER_ABOVE_LAST_CAPACITY = 100.0
MIN_UP_TIME = timedelta(hours=2)


@pytest.fixture
def generator() -> Generator:
    return Generator(name="gen1", nominal_power=NOMINAL_POWER, variable_cost=VARIABLE_COST)


@pytest.fixture
def storage() -> BatteryStorage:
    return BatteryStorage(
        name="bat1",
        battery=Battery(
            capacity=STORAGE_CAPACITY,
            max_charge_power=STORAGE_MAX_CHARGE_POWER,
            max_discharge_power=STORAGE_MAX_DISCHARGE_POWER,
            efficiency_charging=STORAGE_EFFICIENCY,
            efficiency_discharging=STORAGE_EFFICIENCY,
        ),
    )


@pytest.fixture
def storage_initial_state(storage: BatteryStorage) -> StorageInitialState:
    return StorageInitialState(storage=storage, soc=SOC_START)


@pytest.fixture
def load() -> FixedLoad:
    return FixedLoad(name="load1")


@pytest.fixture
def flexible_load() -> FlexibleLoad:
    return FlexibleLoad(name="flex_load1", value_of_consumption=VALUE_OF_CONSUMPTION)


def _flexible_profile(load: FlexibleLoad, lower_bound: list[float]) -> FlexibleLoadProfile:
    upper_bound = [lower_t + FLEXIBLE_RANGE_WIDTH for lower_t in lower_bound]
    return FlexibleLoadProfile(load=load, lower_bound=lower_bound, upper_bound=upper_bound)


@pytest.fixture
def portfolio(generator: Generator, storage: BatteryStorage, load: FixedLoad) -> AssetPortfolio:
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
        ),
        trips=trips,
    )


class TestValidateEnergySystemInputs:
    def test_valid(
        self,
        portfolio: AssetPortfolio,
        scenario: Scenario,
        storage_initial_state: StorageInitialState,
    ) -> None:
        validate_energy_system_inputs(
            portfolio,
            ScenarioSet(scenarios=(scenario,)),
            (),
            HORIZON,
            ConditionSet(initial=(storage_initial_state,)),
        )

    def test_checks_every_entity_against_the_horizon(self, generator: Generator, load: FixedLoad) -> None:
        late_trip = Trip(
            name="late_trip",
            start_time=timedelta(hours=2),
            end_time=timedelta(hours=NUMBER_OF_STEPS + 1),
            energy_consumption=5.0,
        )
        electric_vehicle = _electric_vehicle((late_trip,))
        portfolio = AssetPortfolio([
            generator,
            load,
            electric_vehicle,
            Charger(name="charger1", max_power=CHARGER_MAX_POWER),
        ])
        scenario = Scenario(profiles=(LoadProfile(load=load, values=DEMAND_PROFILE),))
        conditions = ConditionSet(initial=(ElectricVehicleInitialState(vehicle=electric_vehicle, soc=SOC_START),))
        with pytest.raises(OdysValidationError, match="Trip 'late_trip' for vehicle 'ev1' extends beyond"):
            validate_energy_system_inputs(portfolio, ScenarioSet(scenarios=(scenario,)), (), HORIZON, conditions)

    def test_checks_the_conditions(self, portfolio: AssetPortfolio, scenario: Scenario) -> None:
        with pytest.raises(OdysValidationError, match="BatteryStorage 'bat1' needs a StorageInitialState"):
            validate_energy_system_inputs(portfolio, ScenarioSet(scenarios=(scenario,)), (), HORIZON, ConditionSet())

    def test_energy_check_is_skipped_with_markets(
        self,
        storage: BatteryStorage,
        load: FixedLoad,
        storage_initial_state: StorageInitialState,
    ) -> None:
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
            ConditionSet(initial=(storage_initial_state,)),
        )


class TestValidateConditionsReferenceSystemAssets:
    def test_conditions_referencing_system_assets_are_valid(
        self,
        portfolio: AssetPortfolio,
        storage_initial_state: StorageInitialState,
    ) -> None:
        validate_conditions_reference_system_assets(ConditionSet(initial=(storage_initial_state,)), portfolio)

    def test_rejects_condition_for_an_asset_not_in_the_portfolio(self, generator: Generator, load: FixedLoad) -> None:
        other_generator = Generator(name="other", nominal_power=NOMINAL_POWER, variable_cost=VARIABLE_COST)
        conditions = ConditionSet(initial=(GeneratorInitialState(generator=other_generator, power=0.0),))

        with pytest.raises(
            OdysValidationError,
            match="The GeneratorInitialState for 'other' references an asset that is not in the energy system",
        ):
            validate_conditions_reference_system_assets(conditions, AssetPortfolio([generator, load]))

    def test_rejects_condition_for_a_different_asset_with_the_same_name(
        self,
        generator: Generator,
        load: FixedLoad,
    ) -> None:
        copy_with_other_cost = generator.model_copy(update={"variable_cost": VARIABLE_COST + 1})
        conditions = ConditionSet(final=(GeneratorFinalState(generator=copy_with_other_cost, power=0.0),))

        with pytest.raises(
            OdysValidationError,
            match="The GeneratorFinalState for 'gen1' does not reference the asset of that name",
        ):
            validate_conditions_reference_system_assets(conditions, AssetPortfolio([generator, load]))


class TestValidateRequiredInitialConditionsPresent:
    def test_plain_generator_needs_no_initial_state(self, generator: Generator, load: FixedLoad) -> None:
        validate_required_initial_conditions_present(ConditionSet(), AssetPortfolio([generator, load]))

    def test_storage_without_initial_state_is_rejected(self, portfolio: AssetPortfolio) -> None:
        with pytest.raises(
            OdysValidationError,
            match="BatteryStorage 'bat1' needs a StorageInitialState because its state of charge carries over",
        ):
            validate_required_initial_conditions_present(ConditionSet(), portfolio)

    def test_electric_vehicle_without_initial_state_is_rejected(self, load: FixedLoad) -> None:
        portfolio = AssetPortfolio([load, _electric_vehicle(), Charger(name="charger1", max_power=CHARGER_MAX_POWER)])

        with pytest.raises(OdysValidationError, match="ElectricVehicle 'ev1' needs a ElectricVehicleInitialState"):
            validate_required_initial_conditions_present(ConditionSet(), portfolio)

    def test_time_coupled_generator_without_initial_state_is_rejected(self, load: FixedLoad) -> None:
        ramping = Generator(name="ramping", nominal_power=NOMINAL_POWER, variable_cost=VARIABLE_COST, ramp_up=RAMP_UP)

        with pytest.raises(
            OdysValidationError,
            match="Generator 'ramping' needs a GeneratorInitialState because it has ramp_up set",
        ):
            validate_required_initial_conditions_present(ConditionSet(), AssetPortfolio([ramping, load]))

    def test_time_coupled_generator_with_initial_state_is_valid(self, load: FixedLoad) -> None:
        ramping = Generator(name="ramping", nominal_power=NOMINAL_POWER, variable_cost=VARIABLE_COST, ramp_up=RAMP_UP)
        conditions = ConditionSet(initial=(GeneratorInitialState(generator=ramping, power=INITIAL_POWER),))

        validate_required_initial_conditions_present(conditions, AssetPortfolio([ramping, load]))


class TestValidateConditionsFitTheHorizon:
    @pytest.fixture
    def generator_with_min_up_time(self) -> Generator:
        return Generator(
            name="gen1",
            nominal_power=NOMINAL_POWER,
            variable_cost=VARIABLE_COST,
            min_up_time=MIN_UP_TIME,
        )

    def test_whole_steps_are_valid(self, generator_with_min_up_time: Generator) -> None:
        state = GeneratorInitialState(
            generator=generator_with_min_up_time,
            power=INITIAL_POWER,
            time_in_state=timedelta(hours=1),
        )

        validate_conditions_fit_the_run(ConditionSet(initial=(state,)), (Scenario(),), HORIZON)

    def test_partial_step_is_rejected(self, generator_with_min_up_time: Generator) -> None:
        state = GeneratorInitialState(
            generator=generator_with_min_up_time,
            power=INITIAL_POWER,
            time_in_state=timedelta(minutes=30),
        )

        with pytest.raises(
            OdysValidationError,
            match=r"time_in_state=0:30:00, which is not a whole number of timesteps \(1:00:00\)",
        ):
            validate_conditions_fit_the_run(ConditionSet(initial=(state,)), (Scenario(),), HORIZON)


class TestValidateConditionsFitEachScenario:
    def test_final_power_within_last_capacity_is_valid(self, generator: Generator) -> None:
        scenario = Scenario(profiles=(AvailableCapacityProfile(generator=generator, values=CAPACITY_PROFILE),))
        conditions = ConditionSet(final=(GeneratorFinalState(generator=generator, power=CAPACITY_PROFILE[-1]),))

        validate_conditions_fit_the_run(conditions, (scenario,), HORIZON)

    def test_final_power_without_capacity_profile_is_valid(self, generator: Generator) -> None:
        conditions = ConditionSet(final=(GeneratorFinalState(generator=generator, power=NOMINAL_POWER),))

        validate_conditions_fit_the_run(conditions, (Scenario(),), HORIZON)

    def test_final_power_above_last_capacity_is_rejected(self, generator: Generator) -> None:
        capacity = [NOMINAL_POWER, NOMINAL_POWER, NOMINAL_POWER, CAPACITY_PROFILE[0]]
        scenario = Scenario(
            name="low_wind",
            profiles=(AvailableCapacityProfile(generator=generator, values=capacity),),
        )
        conditions = ConditionSet(
            final=(GeneratorFinalState(generator=generator, power=FINAL_POWER_ABOVE_LAST_CAPACITY),),
        )

        with pytest.raises(
            OdysValidationError,
            match=r"Scenario 'low_wind': GeneratorFinalState for generator 'gen1' has power=100.0, "
            r"above its available capacity \(90.0\) at the last timestep",
        ):
            validate_conditions_fit_the_run(conditions, (scenario,), HORIZON)


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
        scenario = Scenario(name="s1", profiles=(_flexible_profile(flexible_load, DEMAND_PROFILE),))
        with pytest.raises(
            OdysValidationError,
            match="Scenario 's1' has a FlexibleLoadProfile for 'flex_load1', which is not in the energy system",
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
        storage: BatteryStorage,
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
        scenario = Scenario(name="s1", profiles=(_flexible_profile(flexible_load, DEMAND_PROFILE),))
        with pytest.raises(OdysValidationError, match=r"is missing a FlexibleLoadProfile for: \['flex_load2'\]"):
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
        scenario = Scenario(name="s1", profiles=(_flexible_profile(flexible_load, [40.0, 50.0]),))
        with pytest.raises(OdysValidationError, match="the FlexibleLoadProfile for 'flex_load1' has 2 values"):
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

    def test_flexible_load_without_market_is_valid(self, flexible_load: FlexibleLoad) -> None:
        validate_has_load_or_market(Scenario(profiles=(_flexible_profile(flexible_load, DEMAND_PROFILE),)), ())

    def test_market_only_no_loads_is_valid(self, market: EnergyMarket) -> None:
        validate_has_load_or_market(Scenario(), (market,))

    def test_no_load_and_no_market(self) -> None:
        with pytest.raises(OdysValidationError, match="Load profile is empty, there is nothing to balance"):
            validate_has_load_or_market(Scenario(), ())


class TestValidateEnoughPowerToMeetDemand:
    def test_valid(self, generator: Generator, storage: BatteryStorage, load: FixedLoad, scenario: Scenario) -> None:
        validate_enough_power_to_meet_demand(scenario, (generator, storage, load), HORIZON)

    def test_market_only_no_loads_is_valid(
        self,
        generator: Generator,
        storage: BatteryStorage,
        market: EnergyMarket,
    ) -> None:
        scenario = Scenario(profiles=(PriceProfile(market=market, values=MARKET_PRICES),))
        validate_enough_power_to_meet_demand(scenario, (generator, storage, market), HORIZON)

    def test_demand_exceeds_capacity(self, generator: Generator, storage: BatteryStorage, load: FixedLoad) -> None:
        scenario = Scenario(name="s1", profiles=(LoadProfile(load=load, values=[80.0, 200.0, 90.0, 100.0]),))
        with pytest.raises(
            OdysValidationError,
            match=r"Infeasible problem in scenario 's1' at time index 1: minimum demand = 200.0.* = 125.0",
        ):
            validate_enough_power_to_meet_demand(scenario, (generator, storage, load), HORIZON)

    def test_demand_is_summed_over_loads(
        self,
        generator: Generator,
        storage: BatteryStorage,
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

    def test_flexible_load_feasible_at_its_lower_bound(
        self,
        generator: Generator,
        storage: BatteryStorage,
        flexible_load: FlexibleLoad,
    ) -> None:
        scenario = Scenario(profiles=(_flexible_profile(flexible_load, [50.0, 120.0, 60.0, 70.0]),))
        validate_enough_power_to_meet_demand(scenario, (generator, storage, flexible_load), HORIZON)

    def test_flexible_load_feasible_with_lower_bound_at_the_limit(
        self,
        generator: Generator,
        storage: BatteryStorage,
        flexible_load: FlexibleLoad,
    ) -> None:
        scenario = Scenario(profiles=(_flexible_profile(flexible_load, [50.0, 125.0, 60.0, 70.0]),))
        validate_enough_power_to_meet_demand(scenario, (generator, storage, flexible_load), HORIZON)

    def test_flexible_load_infeasible_at_its_lower_bound(
        self,
        generator: Generator,
        storage: BatteryStorage,
        flexible_load: FlexibleLoad,
    ) -> None:
        scenario = Scenario(profiles=(_flexible_profile(flexible_load, [50.0, 170.0, 60.0, 70.0]),))
        with pytest.raises(OdysValidationError, match=r"time index 1: minimum demand = 170\.0"):
            validate_enough_power_to_meet_demand(scenario, (generator, storage, flexible_load), HORIZON)

    def test_market_volume_counted_toward_available_power(
        self,
        generator: Generator,
        storage: BatteryStorage,
        market: EnergyMarket,
        load: FixedLoad,
    ) -> None:
        scenario = Scenario(profiles=(LoadProfile(load=load, values=[80.0, 200.0, 90.0, 100.0]),))
        validate_enough_power_to_meet_demand(scenario, (generator, storage, market, load), HORIZON)

    def test_infeasible_even_with_market(
        self,
        generator: Generator,
        storage: BatteryStorage,
        market: EnergyMarket,
        load: FixedLoad,
    ) -> None:
        scenario = Scenario(profiles=(LoadProfile(load=load, values=[80.0, 300.0, 90.0, 100.0]),))
        with pytest.raises(OdysValidationError, match="Infeasible problem"):
            validate_enough_power_to_meet_demand(scenario, (generator, storage, market, load), HORIZON)

    def test_uses_available_capacity_profile_per_timestep(
        self,
        generator: Generator,
        storage: BatteryStorage,
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
    def test_no_loads(self, generator: Generator, storage: BatteryStorage) -> None:
        validate_enough_energy_to_meet_demand(Scenario(), (generator, storage), HORIZON)

    def test_valid(self, generator: Generator, storage: BatteryStorage, load: FixedLoad, scenario: Scenario) -> None:
        validate_enough_energy_to_meet_demand(scenario, (generator, storage, load), HORIZON)

    def test_infeasible_energy_but_feasible_power(self, storage: BatteryStorage, load: FixedLoad) -> None:
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

    def test_flexible_load_lower_bound_used(self, flexible_load: FlexibleLoad) -> None:
        scenario = Scenario(profiles=(_flexible_profile(flexible_load, [10.0, 10.0, 10.0, 10.0]),))
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
