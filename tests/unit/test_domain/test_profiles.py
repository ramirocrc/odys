"""Tests for typed scenario profiles."""

from typing import get_args

import pytest
from pydantic import ValidationError

from odys.domain.entities.fixed_load import FixedLoad
from odys.domain.entities.flexible_load import FlexibleLoad
from odys.domain.entities.generator import Generator
from odys.domain.entities.market import EnergyMarket
from odys.domain.exceptions import OdysValidationError
from odys.domain.profiles import (
    PROFILE_TYPES,
    AvailableCapacityProfile,
    FlexibleLoadProfile,
    LoadProfile,
    PriceProfile,
    Profile,
)

VALUES = [10.0, 20.0, 30.0]
NOMINAL_POWER = 100.0
VARIABLE_COST = 20.0
MAX_TRADING_VOLUME = 50.0
LOWER_BOUND = [5.0, 10.0, 15.0]
UPPER_BOUND = [20.0, 25.0, 30.0]
MIN_LOAD = 5.0
MAX_LOAD = 30.0
VALUE_OF_CONSUMPTION = 50.0
SERIES_FIELDS = {"values", "lower_bound", "upper_bound"}


@pytest.fixture
def fixed_load() -> FixedLoad:
    return FixedLoad(name="load1")


@pytest.fixture
def flexible_load() -> FlexibleLoad:
    return FlexibleLoad(name="flex1", value_of_consumption=VALUE_OF_CONSUMPTION)


@pytest.fixture
def generator() -> Generator:
    return Generator(name="gen1", nominal_power=NOMINAL_POWER, variable_cost=VARIABLE_COST)


@pytest.fixture
def market() -> EnergyMarket:
    return EnergyMarket(name="market1", max_trading_volume_per_step=MAX_TRADING_VOLUME)


class TestProfileEntity:
    def test_demand_of_a_fixed_load(self, fixed_load: FixedLoad) -> None:
        assert LoadProfile(load=fixed_load, values=VALUES).entity == fixed_load

    def test_range_of_a_flexible_load(self, flexible_load: FlexibleLoad) -> None:
        profile = FlexibleLoadProfile(load=flexible_load, lower_bound=LOWER_BOUND, upper_bound=UPPER_BOUND)
        assert profile.entity == flexible_load

    def test_available_capacity_of_a_generator(self, generator: Generator) -> None:
        assert AvailableCapacityProfile(generator=generator, values=VALUES).entity == generator

    def test_price_of_a_market(self, market: EnergyMarket) -> None:
        assert PriceProfile(market=market, values=VALUES).entity == market


class TestProfileRejectsWrongEntityType:
    def test_demand_of_a_generator(self, generator: Generator) -> None:
        with pytest.raises(ValidationError, match="instance of FixedLoad"):
            LoadProfile.model_validate({"load": generator, "values": VALUES})

    def test_demand_of_a_flexible_load(self, flexible_load: FlexibleLoad) -> None:
        with pytest.raises(ValidationError, match="instance of FixedLoad"):
            LoadProfile.model_validate({"load": flexible_load, "values": VALUES})

    def test_range_of_a_fixed_load(self, fixed_load: FixedLoad) -> None:
        with pytest.raises(ValidationError, match="instance of FlexibleLoad"):
            FlexibleLoadProfile.model_validate(
                {"load": fixed_load, "lower_bound": LOWER_BOUND, "upper_bound": UPPER_BOUND},
            )

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


class TestSeriesProfileOperatingConditions:
    def test_number_of_steps_is_the_number_of_values(self, fixed_load: FixedLoad) -> None:
        assert LoadProfile(load=fixed_load, values=VALUES).number_of_steps == len(VALUES)

    def test_operating_values_are_the_values(self, generator: Generator) -> None:
        assert AvailableCapacityProfile(generator=generator, values=VALUES).operating_values == tuple(VALUES)


class TestFlexibleLoadProfileBounds:
    def test_bounds_are_stored_as_float_tuples(self, flexible_load: FlexibleLoad) -> None:
        profile = FlexibleLoadProfile(load=flexible_load, lower_bound=[1, 2], upper_bound=[3, 4])

        assert profile.lower_bound == (1.0, 2.0)
        assert profile.upper_bound == (3.0, 4.0)
        assert all(type(value) is float for value in (*profile.lower_bound, *profile.upper_bound))

    @pytest.mark.parametrize("field", ["lower_bound", "upper_bound"], ids=["lower", "upper"])
    def test_rejects_an_empty_bound(self, flexible_load: FlexibleLoad, field: str) -> None:
        bounds = {"lower_bound": LOWER_BOUND, "upper_bound": UPPER_BOUND} | {field: []}
        with pytest.raises(ValidationError, match="at least 1 item"):
            FlexibleLoadProfile.model_validate({"load": flexible_load, **bounds})

    def test_number_of_steps_is_the_length_of_the_bounds(self, flexible_load: FlexibleLoad) -> None:
        profile = FlexibleLoadProfile(load=flexible_load, lower_bound=LOWER_BOUND, upper_bound=UPPER_BOUND)
        assert profile.number_of_steps == len(LOWER_BOUND)

    def test_operating_values_are_the_lower_bound(self, flexible_load: FlexibleLoad) -> None:
        profile = FlexibleLoadProfile(load=flexible_load, lower_bound=LOWER_BOUND, upper_bound=UPPER_BOUND)
        assert profile.operating_values == tuple(LOWER_BOUND)

    def test_accepts_equal_bounds_and_a_zero_lower_bound(self, flexible_load: FlexibleLoad) -> None:
        profile = FlexibleLoadProfile(load=flexible_load, lower_bound=[0.0, 10.0], upper_bound=[0.0, 10.0])
        assert profile.lower_bound == profile.upper_bound

    @pytest.mark.parametrize(
        ("lower_bound", "upper_bound", "message"),
        [
            ([5.0, 10.0], [20.0], r"Flexible load 'flex1' has 2 lower bound values and 1 upper bound values"),
            ([5.0, -1.0], [20.0, 20.0], r"Flexible load 'flex1' has a negative lower bound \(-1.0\) at time index 1"),
            (
                [5.0, 21.0],
                [20.0, 20.0],
                r"Flexible load 'flex1' has a lower bound \(21.0\) above its upper bound \(20.0\) at time index 1",
            ),
        ],
        ids=["different_lengths", "negative_lower_bound", "lower_above_upper"],
    )
    def test_rejects_bounds_that_are_not_a_range(
        self,
        flexible_load: FlexibleLoad,
        lower_bound: list[float],
        upper_bound: list[float],
        message: str,
    ) -> None:
        with pytest.raises(OdysValidationError, match=message):
            FlexibleLoadProfile(load=flexible_load, lower_bound=lower_bound, upper_bound=upper_bound)


class TestFlexibleLoadProfileWithinLoadLimits:
    @pytest.fixture
    def limited_load(self) -> FlexibleLoad:
        return FlexibleLoad(
            name="flex1",
            min_load=MIN_LOAD,
            max_load=MAX_LOAD,
            value_of_consumption=VALUE_OF_CONSUMPTION,
        )

    def test_accepts_bounds_on_the_limits(self, limited_load: FlexibleLoad) -> None:
        profile = FlexibleLoadProfile(load=limited_load, lower_bound=[MIN_LOAD], upper_bound=[MAX_LOAD])
        assert profile.lower_bound == (MIN_LOAD,)

    def test_rejects_lower_bound_below_min_load(self, limited_load: FlexibleLoad) -> None:
        with pytest.raises(
            OdysValidationError,
            match=r"Flexible load 'flex1' has a lower bound \(4.0\) below min_load \(5.0\) at time index 1",
        ):
            FlexibleLoadProfile(load=limited_load, lower_bound=[MIN_LOAD, 4.0], upper_bound=[MAX_LOAD, MAX_LOAD])

    def test_rejects_upper_bound_above_max_load(self, limited_load: FlexibleLoad) -> None:
        with pytest.raises(
            OdysValidationError,
            match=r"Flexible load 'flex1' has an upper bound \(31.0\) above max_load \(30.0\) at time index 2",
        ):
            FlexibleLoadProfile(load=limited_load, lower_bound=LOWER_BOUND, upper_bound=[20.0, 25.0, 31.0])

    def test_unset_limits_put_no_limit_on_the_bounds(self, flexible_load: FlexibleLoad) -> None:
        profile = FlexibleLoadProfile(load=flexible_load, lower_bound=[0.0], upper_bound=[1000.0])
        assert profile.upper_bound == (1000.0,)


def test_profile_types_apply_to_disjoint_entity_types() -> None:
    entity_types = [entity_type for profile_type in PROFILE_TYPES for entity_type in profile_type.entity_types]

    assert len(entity_types) == len(set(entity_types))


@pytest.mark.parametrize("profile_type", PROFILE_TYPES, ids=lambda profile_type: profile_type.__name__)
def test_profile_type_entity_types_match_its_entity_field(profile_type: type[Profile]) -> None:
    entity_field = next(name for name in profile_type.model_fields if name not in SERIES_FIELDS)
    annotation = profile_type.model_fields[entity_field].annotation
    declared_types = get_args(annotation) or (annotation,)

    assert set(declared_types) == set(profile_type.entity_types)
