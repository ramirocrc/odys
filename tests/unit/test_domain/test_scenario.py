"""Tests for scenarios and scenario sets."""

import pytest
from pydantic import ValidationError

from odys.domain.entities.fixed_load import FixedLoad
from odys.domain.entities.generator import Generator
from odys.domain.entities.market import EnergyMarket
from odys.domain.exceptions import OdysValidationError
from odys.domain.profiles import AvailableCapacityProfile, LoadProfile, PriceProfile
from odys.domain.scenario import Scenario, ScenarioSet

LOAD_PROFILE = [80.0, 120.0, 90.0]
MARKET_PRICES = [10.0, 20.0, 30.0]
CAPACITY_PROFILE = [100.0, 100.0, 100.0]
NOMINAL_POWER = 100.0
VARIABLE_COST = 20.0
MAX_TRADING_VOLUME = 50.0
NUMBER_OF_EQUIPROBABLE_SCENARIOS = 49  # sum([1 / 49] * 49) != 1.0 in floating point


@pytest.fixture
def load() -> FixedLoad:
    return FixedLoad(name="load1")


@pytest.fixture
def generator() -> Generator:
    return Generator(name="gen1", nominal_power=NOMINAL_POWER, variable_cost=VARIABLE_COST)


@pytest.fixture
def market() -> EnergyMarket:
    return EnergyMarket(name="market1", max_trading_volume_per_step=MAX_TRADING_VOLUME)


class TestScenario:
    def test_defaults_to_a_certain_base_scenario_without_profiles(self) -> None:
        scenario = Scenario()
        assert scenario.name == "base"
        assert scenario.probability == 1.0
        assert scenario.profiles == ()

    def test_accepts_profiles_of_every_kind(
        self,
        load: FixedLoad,
        generator: Generator,
        market: EnergyMarket,
    ) -> None:
        demand = LoadProfile(load=load, values=LOAD_PROFILE)
        capacity = AvailableCapacityProfile(generator=generator, values=CAPACITY_PROFILE)
        price = PriceProfile(market=market, values=MARKET_PRICES)

        scenario = Scenario(profiles=(demand, capacity, price))

        assert scenario.profiles == (demand, capacity, price)

    def test_profiles_of_returns_only_profiles_of_that_kind_in_order(
        self,
        load: FixedLoad,
        generator: Generator,
        market: EnergyMarket,
    ) -> None:
        other_load = FixedLoad(name="load2")
        first_demand = LoadProfile(load=load, values=LOAD_PROFILE)
        second_demand = LoadProfile(load=other_load, values=LOAD_PROFILE)
        scenario = Scenario(
            profiles=(
                first_demand,
                AvailableCapacityProfile(generator=generator, values=CAPACITY_PROFILE),
                second_demand,
                PriceProfile(market=market, values=MARKET_PRICES),
            ),
        )

        assert scenario.profiles_of(LoadProfile) == (first_demand, second_demand)
        assert scenario.profiles_of(PriceProfile) == (PriceProfile(market=market, values=MARKET_PRICES),)

    def test_rejects_two_profiles_of_the_same_kind_for_one_entity(self, load: FixedLoad) -> None:
        with pytest.raises(
            OdysValidationError,
            match="Scenario 's1' has more than one profile: LoadProfile for 'load1'",
        ):
            Scenario(
                name="s1",
                profiles=(
                    LoadProfile(load=load, values=LOAD_PROFILE),
                    LoadProfile(load=load, values=LOAD_PROFILE),
                ),
            )

    def test_accepts_profiles_of_different_kinds_for_entities_sharing_a_name(
        self,
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
        assert (
            scenario.profiles_of(PriceProfile)[0].entity.name
            == scenario.profiles_of(AvailableCapacityProfile)[0].entity.name
        )

    @pytest.mark.parametrize("probability", [0.0, 0.5, 1.0])
    def test_accepts_probability_within_bounds(self, probability: float) -> None:
        scenario = Scenario(name="s1", probability=probability)
        assert scenario.probability == probability

    @pytest.mark.parametrize(
        ("probability", "expected_match"),
        [
            (-0.1, "Input should be greater than or equal to 0"),
            (1.1, "Input should be less than or equal to 1"),
        ],
    )
    def test_rejects_probability_out_of_bounds(self, probability: float, expected_match: str) -> None:
        with pytest.raises(ValidationError, match=expected_match):
            Scenario(name="s1", probability=probability)

    def test_round_trips_through_a_dict(
        self,
        load: FixedLoad,
        generator: Generator,
        market: EnergyMarket,
    ) -> None:
        scenario = Scenario(
            name="s1",
            probability=0.5,
            profiles=(
                LoadProfile(load=load, values=LOAD_PROFILE),
                AvailableCapacityProfile(generator=generator, values=CAPACITY_PROFILE),
                PriceProfile(market=market, values=MARKET_PRICES),
            ),
        )
        assert Scenario.model_validate(scenario.model_dump()) == scenario

    def test_is_frozen(self, load: FixedLoad) -> None:
        scenario = Scenario()
        frozen_field = "profiles"
        with pytest.raises(ValidationError, match="Instance is frozen"):
            setattr(scenario, frozen_field, (LoadProfile(load=load, values=LOAD_PROFILE),))

    def test_rejects_unknown_field(self) -> None:
        with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
            Scenario.model_validate({"fixed_load_profiles": {"load1": LOAD_PROFILE}})


class TestScenarioProfileFor:
    def test_returns_the_profile_that_references_the_entity(
        self,
        load: FixedLoad,
        generator: Generator,
        market: EnergyMarket,
    ) -> None:
        capacity = AvailableCapacityProfile(generator=generator, values=CAPACITY_PROFILE)
        price = PriceProfile(market=market, values=MARKET_PRICES)
        scenario = Scenario(profiles=(LoadProfile(load=load, values=LOAD_PROFILE), capacity, price))

        assert scenario.profile_for(generator) == capacity
        assert scenario.profile_for(market) == price

    def test_returns_none_for_an_entity_without_a_profile(self, load: FixedLoad, generator: Generator) -> None:
        scenario = Scenario(profiles=(LoadProfile(load=load, values=LOAD_PROFILE),))

        assert scenario.profile_for(generator) is None

    def test_does_not_match_a_different_entity_with_the_same_name(self, load: FixedLoad) -> None:
        scenario = Scenario(profiles=(LoadProfile(load=load, values=LOAD_PROFILE),))
        market_named_like_load = EnergyMarket(name=load.name, max_trading_volume_per_step=MAX_TRADING_VOLUME)

        assert scenario.profile_for(market_named_like_load) is None


class TestScenarioSet:
    def test_single_scenario_with_probability_one(self) -> None:
        scenario_set = ScenarioSet(scenarios=(Scenario(name="s1"),))
        assert scenario_set.names == ("s1",)

    def test_multiple_scenarios_summing_to_one(self) -> None:
        scenario_set = ScenarioSet(
            scenarios=(
                Scenario(name="s1", probability=0.5),
                Scenario(name="s2", probability=0.3),
                Scenario(name="s3", probability=0.2),
            ),
        )
        assert scenario_set.names == ("s1", "s2", "s3")

    def test_equiprobable_scenarios_with_float_rounding_are_accepted(self) -> None:
        scenarios = tuple(
            Scenario(name=f"s{i}", probability=1 / NUMBER_OF_EQUIPROBABLE_SCENARIOS)
            for i in range(NUMBER_OF_EQUIPROBABLE_SCENARIOS)
        )
        assert len(ScenarioSet(scenarios=scenarios).scenarios) == NUMBER_OF_EQUIPROBABLE_SCENARIOS

    def test_empty_set_raises(self) -> None:
        with pytest.raises(OdysValidationError, match=r"got sum = 0 instead"):
            ScenarioSet(scenarios=())

    @pytest.mark.parametrize(
        ("probabilities", "expected_sum"),
        [
            ((0.3, 0.3), 0.6),
            ((0.6, 0.6), 1.2),
        ],
    )
    def test_probabilities_not_summing_to_one_raises(
        self,
        probabilities: tuple[float, float],
        expected_sum: float,
    ) -> None:
        scenarios = tuple(
            Scenario(name=f"s{i}", probability=probability) for i, probability in enumerate(probabilities)
        )
        with pytest.raises(OdysValidationError, match=rf"got sum = {expected_sum} instead"):
            ScenarioSet(scenarios=scenarios)

    def test_duplicate_names_raise_even_when_probabilities_sum_to_one(self) -> None:
        scenarios = (
            Scenario(name="dup", probability=0.5),
            Scenario(name="dup", probability=0.5),
        )
        with pytest.raises(OdysValidationError, match="must have a unique name"):
            ScenarioSet(scenarios=scenarios)

    def test_sum_check_runs_before_duplicate_name_check(self) -> None:
        """When both checks would fail, the probability-sum error is the one raised."""
        scenarios = (
            Scenario(name="dup", probability=0.3),
            Scenario(name="dup", probability=0.3),
        )
        with pytest.raises(OdysValidationError, match=r"got sum = 0\.6 instead"):
            ScenarioSet(scenarios=scenarios)
