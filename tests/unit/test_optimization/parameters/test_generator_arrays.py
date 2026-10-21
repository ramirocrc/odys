"""Unit tests for the generator arrays and state arrays."""

from datetime import timedelta

import numpy as np
import pytest

from odys.domain.conditions import ConditionSet, GeneratorFinalState, GeneratorInitialState
from odys.domain.entities.commitment import Commitment
from odys.domain.entities.generator import Generator
from odys.domain.horizon import Horizon
from odys.domain.scenario import Scenario, ScenarioSet
from odys.parameters.context import ModelContext
from odys.parameters.coordinates import Coordinates
from odys.parameters.entity_arrays import (
    CommitmentArrays,
    GeneratorArrays,
    GeneratorStateArrays,
    generator_state_arrays,
)
from odys.parameters.vectorize import vectorize

GENERATOR_DIMENSION = "generator"

STANDARD_NOMINAL_POWER = 100.0
STANDARD_VARIABLE_COST = 20.0
EXPLICIT_SHUTDOWN_COST = 15.0
HALF_HOUR = timedelta(minutes=30)
EXPLICIT_MIN_DOWN_TIME = timedelta(minutes=90)
EXPLICIT_MIN_DOWN_STEPS = 3
INITIAL_POWER = 40.0
TIME_IN_STATE = timedelta(hours=1)
STEPS_IN_STATE = 2
FINAL_POWER = 30.0
EXPLICIT_RAMP_UP = 10.0


def _generator_arrays(generators: list[Generator]) -> GeneratorArrays:
    return vectorize(GeneratorArrays, generators, Coordinates.of_entities(GENERATOR_DIMENSION, generators))


def _commitment_arrays(generators: list[Generator]) -> CommitmentArrays:
    return vectorize(
        CommitmentArrays,
        [generator.commitment for generator in generators],
        Coordinates.of_entities(GENERATOR_DIMENSION, generators),
    )


def _state_arrays(generators: list[Generator], condition_set: ConditionSet) -> GeneratorStateArrays:
    context = ModelContext(
        horizon=Horizon(timestep=HALF_HOUR, number_of_steps=4),
        scenario_set=ScenarioSet(scenarios=(Scenario(),)),
        condition_set=condition_set,
    )
    return generator_state_arrays(generators, Coordinates.of_entities(GENERATOR_DIMENSION, generators), context)


@pytest.fixture
def generator_with_shutdown_cost() -> Generator:
    return Generator(
        name="gen_with_shutdown_cost",
        nominal_power=STANDARD_NOMINAL_POWER,
        variable_cost=STANDARD_VARIABLE_COST,
        commitment=Commitment(shutdown_cost=EXPLICIT_SHUTDOWN_COST),
    )


@pytest.fixture
def generator_without_shutdown_cost() -> Generator:
    return Generator(
        name="gen_without_shutdown_cost",
        nominal_power=STANDARD_NOMINAL_POWER,
        variable_cost=STANDARD_VARIABLE_COST,
    )


def test_shutdown_cost_reflects_explicit_value(generator_with_shutdown_cost: Generator) -> None:
    params = _commitment_arrays([generator_with_shutdown_cost])

    value = params.shutdown_cost.sel(generator="gen_with_shutdown_cost").item()

    assert value == EXPLICIT_SHUTDOWN_COST


def test_shutdown_cost_defaults_to_zero_when_not_set(generator_without_shutdown_cost: Generator) -> None:
    params = _commitment_arrays([generator_without_shutdown_cost])

    value = params.shutdown_cost.sel(generator="gen_without_shutdown_cost").item()

    assert value == 0.0


def test_shutdown_cost_preserves_explicit_values_alongside_defaulted_ones(
    generator_with_shutdown_cost: Generator,
    generator_without_shutdown_cost: Generator,
) -> None:
    params = _commitment_arrays([generator_with_shutdown_cost, generator_without_shutdown_cost])

    assert params.shutdown_cost.sel(generator="gen_with_shutdown_cost").item() == EXPLICIT_SHUTDOWN_COST
    assert params.shutdown_cost.sel(generator="gen_without_shutdown_cost").item() == 0.0


def test_min_down_steps_converts_the_min_down_time_with_the_timestep() -> None:
    generator = Generator(
        name="gen_with_min_down_time",
        nominal_power=STANDARD_NOMINAL_POWER,
        variable_cost=STANDARD_VARIABLE_COST,
        commitment=Commitment(min_down_time=EXPLICIT_MIN_DOWN_TIME),
    )
    states = _state_arrays([generator], ConditionSet())

    assert states.commitment.min_down_steps.sel(generator="gen_with_min_down_time").item() == EXPLICIT_MIN_DOWN_STEPS


def test_min_up_and_down_steps_default_to_one_when_not_set(generator_without_shutdown_cost: Generator) -> None:
    states = _state_arrays([generator_without_shutdown_cost], ConditionSet())

    assert states.commitment.min_up_steps.sel(generator="gen_without_shutdown_cost").item() == 1
    assert states.commitment.min_down_steps.sel(generator="gen_without_shutdown_cost").item() == 1


def test_state_arrays_read_the_initial_and_final_state(generator_with_shutdown_cost: Generator) -> None:
    condition_set = ConditionSet(
        initial=(
            GeneratorInitialState(
                generator=generator_with_shutdown_cost,
                power=INITIAL_POWER,
                time_in_state=TIME_IN_STATE,
            ),
        ),
        final=(GeneratorFinalState(generator=generator_with_shutdown_cost, power=FINAL_POWER),),
    )
    states = _state_arrays([generator_with_shutdown_cost], condition_set)
    selection = {"generator": "gen_with_shutdown_cost"}

    assert states.initial_power.sel(selection).item() == pytest.approx(INITIAL_POWER)
    assert states.commitment.initial_steps_in_state.sel(selection).item() == STEPS_IN_STATE
    assert states.final_power.sel(selection).item() == pytest.approx(FINAL_POWER)


def test_state_arrays_without_conditions_start_off_for_ever_with_no_final_power(
    generator_without_shutdown_cost: Generator,
) -> None:
    states = _state_arrays([generator_without_shutdown_cost], ConditionSet())
    selection = {"generator": "gen_without_shutdown_cost"}

    assert states.initial_power.sel(selection).item() == 0.0
    assert states.commitment.initial_steps_in_state.sel(selection).item() == np.inf
    assert bool(states.final_power.sel(selection).isnull())


def test_state_arrays_without_time_in_state_count_unlimited_steps(generator_with_shutdown_cost: Generator) -> None:
    condition_set = ConditionSet(initial=(GeneratorInitialState(generator=generator_with_shutdown_cost, power=0.0),))

    states = _state_arrays([generator_with_shutdown_cost], condition_set)

    assert states.commitment.initial_steps_in_state.sel(generator="gen_with_shutdown_cost").item() == np.inf


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
