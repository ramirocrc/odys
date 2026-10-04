"""Unit tests for the generator arrays."""

import pytest

from odys.domain.entities.generator import Generator
from odys.parameters.coordinates import Coordinates
from odys.parameters.dimensions import ModelDimension
from odys.parameters.entity_arrays import GeneratorArrays
from odys.parameters.vectorize import vectorize

STANDARD_NOMINAL_POWER = 100.0
STANDARD_VARIABLE_COST = 20.0
EXPLICIT_SHUTDOWN_COST = 15.0
EXPLICIT_MIN_DOWN_TIME = 3
EXPLICIT_RAMP_UP = 10.0


def _generator_arrays(generators: list[Generator]) -> GeneratorArrays:
    return vectorize(GeneratorArrays, generators, Coordinates.of_entities(ModelDimension.Generators, generators))


@pytest.fixture
def generator_with_shutdown_cost() -> Generator:
    return Generator(
        name="gen_with_shutdown_cost",
        nominal_power=STANDARD_NOMINAL_POWER,
        variable_cost=STANDARD_VARIABLE_COST,
        shutdown_cost=EXPLICIT_SHUTDOWN_COST,
    )


@pytest.fixture
def generator_without_shutdown_cost() -> Generator:
    return Generator(
        name="gen_without_shutdown_cost",
        nominal_power=STANDARD_NOMINAL_POWER,
        variable_cost=STANDARD_VARIABLE_COST,
    )


def test_shutdown_cost_reflects_explicit_value(generator_with_shutdown_cost: Generator) -> None:
    params = _generator_arrays([generator_with_shutdown_cost])

    value = params.shutdown_cost.sel(generator="gen_with_shutdown_cost").item()

    assert value == EXPLICIT_SHUTDOWN_COST


def test_shutdown_cost_defaults_to_zero_when_not_set(generator_without_shutdown_cost: Generator) -> None:
    params = _generator_arrays([generator_without_shutdown_cost])

    value = params.shutdown_cost.sel(generator="gen_without_shutdown_cost").item()

    assert value == 0.0


def test_shutdown_cost_preserves_explicit_values_alongside_defaulted_ones(
    generator_with_shutdown_cost: Generator,
    generator_without_shutdown_cost: Generator,
) -> None:
    params = _generator_arrays([generator_with_shutdown_cost, generator_without_shutdown_cost])

    assert params.shutdown_cost.sel(generator="gen_with_shutdown_cost").item() == EXPLICIT_SHUTDOWN_COST
    assert params.shutdown_cost.sel(generator="gen_without_shutdown_cost").item() == 0.0


def test_min_down_time_reflects_explicit_value() -> None:
    generator = Generator(
        name="gen_with_min_down_time",
        nominal_power=STANDARD_NOMINAL_POWER,
        variable_cost=STANDARD_VARIABLE_COST,
        min_down_time=EXPLICIT_MIN_DOWN_TIME,
    )
    params = _generator_arrays([generator])

    value = params.min_down_time.sel(generator="gen_with_min_down_time").item()

    assert value == EXPLICIT_MIN_DOWN_TIME


def test_min_down_time_defaults_to_one_when_not_set() -> None:
    generator = Generator(
        name="gen_without_min_down_time",
        nominal_power=STANDARD_NOMINAL_POWER,
        variable_cost=STANDARD_VARIABLE_COST,
    )
    params = _generator_arrays([generator])

    value = params.min_down_time.sel(generator="gen_without_min_down_time").item()

    assert value == 1


def test_unset_ramp_up_becomes_nan_in_a_float_array(generator_without_shutdown_cost: Generator) -> None:
    with_ramp = generator_without_shutdown_cost.model_copy(
        update={"name": "gen_with_ramp", "ramp_up": EXPLICIT_RAMP_UP},
    )
    params = _generator_arrays([generator_without_shutdown_cost, with_ramp])

    assert params.ramp_up.dtype.kind == "f"
    assert bool(params.ramp_up.sel(generator="gen_without_shutdown_cost").isnull())
    assert params.ramp_up.sel(generator="gen_with_ramp").item() == EXPLICIT_RAMP_UP


def test_ramp_down_unset_for_every_generator_is_all_nan(generator_without_shutdown_cost: Generator) -> None:
    params = _generator_arrays([generator_without_shutdown_cost])

    assert params.ramp_down.dtype.kind == "f"
    assert bool(params.ramp_down.isnull().all())
