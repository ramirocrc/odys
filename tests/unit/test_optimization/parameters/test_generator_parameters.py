import pytest

from odys.domain.entities.generator import Generator
from odys.optimization.parameters.generator_parameters import GeneratorParameters

STANDARD_NOMINAL_POWER = 100.0
STANDARD_VARIABLE_COST = 20.0
EXPLICIT_SHUTDOWN_COST = 15.0


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
