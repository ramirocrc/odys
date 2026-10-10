"""Unit tests for the model context: coordinates, step length, probabilities and profiles."""

from datetime import timedelta

import numpy as np
import pytest
import xarray as xr

from odys.domain.entities.fixed_load import FixedLoad
from odys.domain.entities.generator import Generator
from odys.domain.exceptions import OdysError
from odys.domain.horizon import Horizon
from odys.domain.profiles import AvailableCapacityProfile, LoadProfile
from odys.domain.scenario import Scenario, ScenarioSet
from odys.parameters.context import ModelContext
from odys.parameters.coordinates import Coordinates
from odys.parameters.dimensions import ModelDimension

NUMBER_OF_STEPS = 3
HALF_HOUR = timedelta(minutes=30)
HOURS_PER_HALF_HOUR = 0.5
LOW_PROBABILITY = 0.25
HIGH_PROBABILITY = 0.75
FIRST_LOAD = (10.0, 20.0, 30.0)
SECOND_LOAD = (1.0, 2.0, 3.0)
CAPACITY = (40.0, 50.0, 60.0)
NOMINAL_POWER = 100.0

FIRST = FixedLoad(name="load_a")
SECOND = FixedLoad(name="load_b")
GENERATOR = Generator(name="gen", nominal_power=NOMINAL_POWER, variable_cost=1.0)
LOAD_DIMENSION = "fixed_load"
GENERATOR_DIMENSION = "generator"
LOAD_COORDINATES = Coordinates.of_entities(LOAD_DIMENSION, [FIRST, SECOND])
GENERATOR_COORDINATES = Coordinates.of_entities(GENERATOR_DIMENSION, [GENERATOR])


def _context(*scenarios: Scenario) -> ModelContext:
    return ModelContext(
        horizon=Horizon(timestep=HALF_HOUR, number_of_steps=NUMBER_OF_STEPS),
        scenario_set=ScenarioSet(scenarios=scenarios),
    )


@pytest.fixture
def context() -> ModelContext:
    profiles = (
        LoadProfile(load=SECOND, values=SECOND_LOAD),
        LoadProfile(load=FIRST, values=FIRST_LOAD),
        AvailableCapacityProfile(generator=GENERATOR, values=CAPACITY),
    )
    return _context(
        Scenario(name="low", probability=LOW_PROBABILITY, profiles=profiles),
        Scenario(name="high", probability=HIGH_PROBABILITY, profiles=profiles[:2]),
    )


def test_context_time_labels_are_strings(context: ModelContext) -> None:
    assert context.time.dimension == ModelDimension.Time
    assert context.time.labels == ("0", "1", "2")


def test_context_scenario_labels_follow_scenario_order(context: ModelContext) -> None:
    assert context.scenarios.labels == ("low", "high")


def test_context_timestep_hours(context: ModelContext) -> None:
    assert context.timestep_hours == pytest.approx(HOURS_PER_HALF_HOUR)


def test_context_probabilities(context: ModelContext) -> None:
    expected = xr.DataArray([LOW_PROBABILITY, HIGH_PROBABILITY], coords={"scenario": ["low", "high"]})
    xr.testing.assert_allclose(context.probabilities, expected)


def test_context_indexes_only_scenario_and_time() -> None:
    assert set(ModelContext.model_fields) == {"horizon", "scenario_set"}


def test_context_profiles_follow_entity_order_not_profile_order(context: ModelContext) -> None:
    profiles = context.profiles(LoadProfile, [FIRST, SECOND], LOAD_COORDINATES)

    expected = xr.DataArray(
        [[FIRST_LOAD, SECOND_LOAD], [FIRST_LOAD, SECOND_LOAD]],
        coords={"scenario": ["low", "high"], "fixed_load": ["load_a", "load_b"], "time": ["0", "1", "2"]},
    )
    xr.testing.assert_allclose(profiles, expected)


def test_context_profiles_use_default_for_entity_without_profile(context: ModelContext) -> None:
    profiles = context.profiles(AvailableCapacityProfile, [GENERATOR], GENERATOR_COORDINATES, default=np.inf)

    expected = xr.DataArray(
        [[CAPACITY], [(np.inf,) * NUMBER_OF_STEPS]],
        coords={"scenario": ["low", "high"], "generator": ["gen"], "time": ["0", "1", "2"]},
    )
    xr.testing.assert_allclose(profiles, expected)


def test_context_profiles_without_default_raise_for_missing_profile(context: ModelContext) -> None:
    with pytest.raises(OdysError, match="Scenario 'high' has no AvailableCapacityProfile for 'gen'"):
        context.profiles(AvailableCapacityProfile, [GENERATOR], GENERATOR_COORDINATES)


def test_context_profiles_match_the_entity_not_only_its_name() -> None:
    copy_with_other_power = GENERATOR.model_copy(update={"nominal_power": NOMINAL_POWER / 2})
    context = _context(Scenario(profiles=(AvailableCapacityProfile(generator=GENERATOR, values=CAPACITY),)))

    profiles = context.profiles(
        AvailableCapacityProfile,
        [copy_with_other_power],
        Coordinates.of_entities(GENERATOR_DIMENSION, [copy_with_other_power]),
        default=0.0,
    )

    assert float(profiles.sum()) == pytest.approx(0.0)


def test_context_variable_coords_are_scenario_time_then_entity_dimensions(context: ModelContext) -> None:
    coords = context.variable_coords(GENERATOR_COORDINATES)

    assert list(coords) == ["scenario", "time", "generator"]
    assert coords["generator"] == ["gen"]
    assert coords["time"] == ["0", "1", "2"]
