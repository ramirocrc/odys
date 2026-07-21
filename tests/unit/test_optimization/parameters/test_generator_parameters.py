import pytest

from odys.domain.entities.generator import Generator
from odys.optimization.parameters.generator_parameters import GeneratorParameters

STANDARD_NOMINAL_POWER = 100.0
STANDARD_VARIABLE_COST = 20.0
EXPLICIT_SHUTDOWN_COST = 15.0
EXPLICIT_MIN_DOWN_TIME = 3


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
    params = GeneratorParameters([generator_with_shutdown_cost])

    value = params.shutdown_cost.sel(generator="gen_with_shutdown_cost").item()

    assert value == EXPLICIT_SHUTDOWN_COST


def test_shutdown_cost_defaults_to_zero_when_not_set(generator_without_shutdown_cost: Generator) -> None:
    params = GeneratorParameters([generator_without_shutdown_cost])

    value = params.shutdown_cost.sel(generator="gen_without_shutdown_cost").item()

    assert value == 0.0


def test_shutdown_cost_preserves_explicit_values_alongside_defaulted_ones(
    generator_with_shutdown_cost: Generator,
    generator_without_shutdown_cost: Generator,
) -> None:
    params = GeneratorParameters([generator_with_shutdown_cost, generator_without_shutdown_cost])

    assert params.shutdown_cost.sel(generator="gen_with_shutdown_cost").item() == EXPLICIT_SHUTDOWN_COST
    assert params.shutdown_cost.sel(generator="gen_without_shutdown_cost").item() == 0.0


def test_min_down_time_reflects_explicit_value() -> None:
    generator = Generator(
        name="gen_with_min_down_time",
        nominal_power=STANDARD_NOMINAL_POWER,
        variable_cost=STANDARD_VARIABLE_COST,
        min_down_time=EXPLICIT_MIN_DOWN_TIME,
    )
    params = GeneratorParameters([generator])

    value = params.min_down_time.sel(generator="gen_with_min_down_time").item()

    assert value == EXPLICIT_MIN_DOWN_TIME


def test_min_down_time_defaults_to_one_when_not_set() -> None:
    generator = Generator(
        name="gen_without_min_down_time",
        nominal_power=STANDARD_NOMINAL_POWER,
        variable_cost=STANDARD_VARIABLE_COST,
    )
    params = GeneratorParameters([generator])

    value = params.min_down_time.sel(generator="gen_without_min_down_time").item()

    assert value == 1
