from datetime import timedelta

import pytest
from pydantic import ValidationError

from odys.domain.entities.commitment import Commitment
from odys.domain.entities.generator import Generator
from odys.domain.exceptions import OdysValidationError
from odys.domain.horizon import Horizon

NOMINAL_POWER = 100.0
VARIABLE_COST = 50.0
RAMP_UP = 50.0
RAMP_DOWN = 40.0
MIN_UP_TIME = timedelta(hours=3)
NUMBER_OF_STEPS = 24
MIN_POWER = 20.0
STARTUP_COST = 100.0
BASE_PARAMS = {"name": "test_generator", "nominal_power": NOMINAL_POWER, "variable_cost": VARIABLE_COST}


@pytest.mark.parametrize(
    ("param_name", "invalid_value", "expected_match"),
    [
        ("nominal_power", 0.0, "Input should be greater than 0"),
        ("nominal_power", -10.0, "Input should be greater than 0"),
        ("variable_cost", -5.0, "Input should be greater than or equal to 0"),
        ("ramp_up", -10.0, "Input should be greater than or equal to 0"),
        ("ramp_down", -10.0, "Input should be greater than or equal to 0"),
        ("min_power", -5.0, "Input should be greater than or equal to 0"),
    ],
)
def test_generator_creation_with_invalid_parameter_raises_error(
    param_name: str,
    invalid_value: float,
    expected_match: str,
) -> None:
    with pytest.raises(ValidationError, match=expected_match):
        Generator.model_validate({**BASE_PARAMS, param_name: invalid_value})


def test_generator_creation_with_minimal_required_fields() -> None:
    gen = Generator(name="test_generator", nominal_power=NOMINAL_POWER, variable_cost=VARIABLE_COST)

    assert gen.name == "test_generator"
    assert gen.nominal_power == NOMINAL_POWER
    assert gen.variable_cost == VARIABLE_COST
    assert gen.ramp_up is None
    assert gen.ramp_down is None
    assert gen.min_power == 0.0


def test_generator_commitment_defaults_to_switching_freely() -> None:
    gen = Generator(name="test_generator", nominal_power=NOMINAL_POWER, variable_cost=VARIABLE_COST)

    assert gen.commitment == Commitment()


def test_generator_creation_with_all_optional_fields() -> None:
    commitment = Commitment(min_up_time=MIN_UP_TIME, startup_cost=STARTUP_COST)
    gen = Generator(
        name="test_gen",
        nominal_power=200.0,
        variable_cost=30.0,
        ramp_up=RAMP_UP,
        ramp_down=RAMP_DOWN,
        min_power=MIN_POWER,
        commitment=commitment,
    )

    assert gen.ramp_up == RAMP_UP
    assert gen.ramp_down == RAMP_DOWN
    assert gen.min_power == MIN_POWER
    assert gen.commitment == commitment


@pytest.mark.parametrize("field", ["ramp_up", "ramp_down"])
def test_generator_ramp_can_be_zero(field: str) -> None:
    gen = Generator.model_validate({**BASE_PARAMS, field: 0.0})

    assert getattr(gen, field) == 0.0


@pytest.mark.parametrize("field", ["min_up_time", "min_down_time", "startup_cost", "shutdown_cost"])
def test_generator_rejects_commitment_fields_outside_its_commitment(field: str) -> None:
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        Generator.model_validate({**BASE_PARAMS, field: MIN_UP_TIME})


def test_generator_validate_horizon_accepts_whole_step_min_times() -> None:
    gen = Generator.model_validate({**BASE_PARAMS, "commitment": Commitment(min_up_time=MIN_UP_TIME)})

    gen.validate_horizon(Horizon(timestep=timedelta(hours=1), number_of_steps=NUMBER_OF_STEPS))


def test_generator_validate_horizon_names_the_generator_for_a_min_time_not_a_whole_number_of_steps() -> None:
    gen = Generator.model_validate({**BASE_PARAMS, "commitment": Commitment(min_up_time=timedelta(minutes=90))})

    with pytest.raises(
        OdysValidationError,
        match=r"Generator 'test_generator' has min_up_time=1:30:00, which is not a whole number of timesteps",
    ):
        gen.validate_horizon(Horizon(timestep=timedelta(hours=1), number_of_steps=NUMBER_OF_STEPS))
