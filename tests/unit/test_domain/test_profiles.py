"""Tests for typed scenario profiles."""

from typing import get_args

import pytest
from pydantic import ValidationError

from odys.domain.entities.fixed_load import FixedLoad
from odys.domain.entities.flexible_load import FlexibleLoad
from odys.domain.entities.generator import Generator
from odys.domain.entities.market import EnergyMarket
from odys.domain.exceptions import OdysValidationError
from odys.domain.profiles import PROFILE_TYPES, AvailableCapacityProfile, LoadProfile, PriceProfile, Profile

VALUES = [10.0, 20.0, 30.0]
NOMINAL_POWER = 100.0
VARIABLE_COST = 20.0
MAX_TRADING_VOLUME = 50.0
MAX_DECREASE = 5.0


@pytest.fixture
def fixed_load() -> FixedLoad:
    return FixedLoad(name="load1")


@pytest.fixture
def flexible_load() -> FlexibleLoad:
    return FlexibleLoad(name="flex1", max_increase=10.0, max_decrease=MAX_DECREASE, value_of_consumption=50.0)


@pytest.fixture
def generator() -> Generator:
    return Generator(name="gen1", nominal_power=NOMINAL_POWER, variable_cost=VARIABLE_COST)


@pytest.fixture
def market() -> EnergyMarket:
    return EnergyMarket(name="market1", max_trading_volume_per_step=MAX_TRADING_VOLUME)


class TestProfileEntity:
    def test_demand_of_a_fixed_load(self, fixed_load: FixedLoad) -> None:
        assert LoadProfile(load=fixed_load, values=VALUES).entity == fixed_load

    def test_demand_of_a_flexible_load(self, flexible_load: FlexibleLoad) -> None:
        assert LoadProfile(load=flexible_load, values=VALUES).entity == flexible_load

    def test_available_capacity_of_a_generator(self, generator: Generator) -> None:
        assert AvailableCapacityProfile(generator=generator, values=VALUES).entity == generator

    def test_price_of_a_market(self, market: EnergyMarket) -> None:
        assert PriceProfile(market=market, values=VALUES).entity == market


class TestProfileRejectsWrongEntityType:
    def test_demand_of_a_generator(self, generator: Generator) -> None:
        with pytest.raises(ValidationError, match="instance of FixedLoad"):
            LoadProfile.model_validate({"load": generator, "values": VALUES})

    def test_available_capacity_of_a_load(self, fixed_load: FixedLoad) -> None:
        with pytest.raises(ValidationError, match="instance of Generator"):
            AvailableCapacityProfile.model_validate({"generator": fixed_load, "values": VALUES})

    def test_price_of_a_generator(self, generator: Generator) -> None:
        with pytest.raises(ValidationError, match="instance of EnergyMarket"):
            PriceProfile.model_validate({"market": generator, "values": VALUES})


class TestProfileValues:
    def test_values_are_stored_as_a_float_tuple(self, fixed_load: FixedLoad) -> None:
        demand = LoadProfile(load=fixed_load, values=[1, 2, 3])
        assert demand.values == (1.0, 2.0, 3.0)
        assert all(type(value) is float for value in demand.values)

    def test_rejects_empty_values(self, fixed_load: FixedLoad) -> None:
        with pytest.raises(ValidationError, match="at least 1 item"):
            LoadProfile(load=fixed_load, values=[])

    def test_is_frozen(self, fixed_load: FixedLoad) -> None:
        demand = LoadProfile(load=fixed_load, values=VALUES)
        frozen_field = "values"
        with pytest.raises(ValidationError, match="Instance is frozen"):
            setattr(demand, frozen_field, (1.0,))

    def test_rejects_unknown_field(self, fixed_load: FixedLoad) -> None:
        with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
            LoadProfile.model_validate({"load": fixed_load, "values": VALUES, "unit": "MW"})


class TestAvailableCapacityWithinNominalPower:
    @pytest.mark.parametrize("values", [[0.0, NOMINAL_POWER], [NOMINAL_POWER / 2]], ids=["bounds", "inside"])
    def test_accepts_values_from_zero_to_nominal_power(self, generator: Generator, values: list[float]) -> None:
        assert AvailableCapacityProfile(generator=generator, values=values).values == tuple(values)

    @pytest.mark.parametrize("value", [-1.0, NOMINAL_POWER + 1], ids=["negative", "above_nominal_power"])
    def test_rejects_values_outside_zero_to_nominal_power(self, generator: Generator, value: float) -> None:
        with pytest.raises(
            OdysValidationError,
            match=rf"Available capacity value {value} for asset 'gen1' is invalid.*\({NOMINAL_POWER}\)",
        ):
            AvailableCapacityProfile(generator=generator, values=[NOMINAL_POWER, value])


class TestFlexibleLoadProfileCoversMaxDecrease:
    def test_accepts_base_equal_to_max_decrease(self, flexible_load: FlexibleLoad) -> None:
        values = [MAX_DECREASE, *VALUES]
        assert LoadProfile(load=flexible_load, values=values).values == tuple(values)

    def test_rejects_base_below_max_decrease(self, flexible_load: FlexibleLoad) -> None:
        below_max_decrease = MAX_DECREASE - 1
        with pytest.raises(
            OdysValidationError,
            match=r"Flexible load 'flex1' has max_decrease \(5.0\) greater than the base profile value \(4.0\) "
            r"at time index 1\. This would allow actual load to go negative",
        ):
            LoadProfile(load=flexible_load, values=[MAX_DECREASE, below_max_decrease])

    def test_fixed_load_profile_has_no_lower_bound_from_the_load(self, fixed_load: FixedLoad) -> None:
        assert LoadProfile(load=fixed_load, values=[0.0]).values == (0.0,)


def test_profile_types_apply_to_disjoint_entity_types() -> None:
    entity_types = [entity_type for profile_type in PROFILE_TYPES for entity_type in profile_type.entity_types]

    assert len(entity_types) == len(set(entity_types))


@pytest.mark.parametrize("profile_type", PROFILE_TYPES, ids=lambda profile_type: profile_type.__name__)
def test_profile_type_entity_types_match_its_entity_field(profile_type: type[Profile]) -> None:
    entity_field = next(name for name in profile_type.model_fields if name != "values")
    annotation = profile_type.model_fields[entity_field].annotation
    declared_types = get_args(annotation) or (annotation,)

    assert set(declared_types) == set(profile_type.entity_types)
