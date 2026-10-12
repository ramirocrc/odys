from datetime import timedelta
from typing import Any, TypedDict, cast

import pytest
from pydantic import ValidationError

from odys.domain.entities.generator import Generator
from odys.domain.exceptions import OdysValidationError
from odys.domain.horizon import Horizon


class GeneratorBaseParams(TypedDict):
    name: str
    nominal_power: float
    variable_cost: float


class GeneratorParams(GeneratorBaseParams, total=False):
    ramp_up: float | None
    ramp_down: float | None
    min_up_time: timedelta | None
    min_down_time: timedelta | None
    min_power: float
    startup_cost: float
    shutdown_cost: float


NOMINAL_POWER = 100.0
VARIABLE_COST = 50.0
RAMP_UP = 50.0
RAMP_DOWN = 40.0
MIN_UP_TIME = timedelta(hours=3)
MIN_DOWN_TIME = timedelta(hours=2)
NUMBER_OF_STEPS = 24
MIN_POWER = 20.0
STARTUP_COST = 100.0
SHUTDOWN_COST = 50.0


@pytest.fixture
def generator_base_params() -> GeneratorBaseParams:
    return {
        "name": "test_generator",
        "nominal_power": NOMINAL_POWER,
        "variable_cost": VARIABLE_COST,
    }


@pytest.mark.parametrize(
    ("param_name", "invalid_value", "expected_match"),
    [
        ("nominal_power", 0.0, "Input should be greater than 0"),
        ("nominal_power", -10.0, "Input should be greater than 0"),
        ("variable_cost", -5.0, "Input should be greater than or equal to 0"),
        ("ramp_up", -10.0, "Input should be greater than or equal to 0"),
        ("ramp_down", -10.0, "Input should be greater than or equal to 0"),
        ("min_up_time", timedelta(0), "Input should be greater than 0"),
        ("min_down_time", timedelta(hours=-1), "Input should be greater than 0"),
        ("min_power", -5.0, "Input should be greater than or equal to 0"),
        ("startup_cost", -10.0, "Input should be greater than or equal to 0"),
        ("shutdown_cost", -10.0, "Input should be greater than or equal to 0"),
    ],
)
def test_generator_creation_with_invalid_parameter_raises_error(
    param_name: str,
    invalid_value: float,
    expected_match: str,
    generator_base_params: GeneratorBaseParams,
) -> None:
    base_params: dict[str, Any] = {**generator_base_params}
    base_params[param_name] = invalid_value
    with pytest.raises(ValidationError, match=expected_match):
        Generator(**cast("GeneratorParams", base_params))


def test_generator_creation_with_minimal_required_fields() -> None:
    base_params: GeneratorParams = {
        "name": "test_generator",
        "nominal_power": NOMINAL_POWER,
        "variable_cost": VARIABLE_COST,
        "ramp_up": None,
        "ramp_down": None,
        "min_up_time": None,
        "min_down_time": None,
        "min_power": 0.0,
        "startup_cost": 0.0,
        "shutdown_cost": 0.0,
    }
    gen = Generator(**base_params)
    assert gen.name == "test_generator"
    assert gen.nominal_power == NOMINAL_POWER
    assert gen.variable_cost == VARIABLE_COST
    assert gen.ramp_up is None
    assert gen.ramp_down is None
    assert gen.min_up_time is None
    assert gen.min_down_time is None
    assert gen.min_power == 0.0
    assert gen.startup_cost == 0.0
    assert gen.shutdown_cost == 0.0


def test_generator_creation_with_all_optional_fields() -> None:
    gen = Generator(
        name="test_gen",
        nominal_power=200.0,
        variable_cost=30.0,
        ramp_up=RAMP_UP,
        ramp_down=RAMP_DOWN,
        min_up_time=MIN_UP_TIME,
        min_down_time=MIN_DOWN_TIME,
        min_power=MIN_POWER,
        startup_cost=STARTUP_COST,
        shutdown_cost=SHUTDOWN_COST,
    )
    assert gen.ramp_up == RAMP_UP
    assert gen.ramp_down == RAMP_DOWN
    assert gen.min_up_time == MIN_UP_TIME
    assert gen.min_down_time == MIN_DOWN_TIME
    assert gen.min_power == MIN_POWER
    assert gen.startup_cost == STARTUP_COST
    assert gen.shutdown_cost == SHUTDOWN_COST


def test_generator_ramp_up_can_be_zero(
    generator_base_params: GeneratorBaseParams,
) -> None:
    base_params: GeneratorParams = {
        "name": generator_base_params["name"],
        "nominal_power": generator_base_params["nominal_power"],
        "variable_cost": generator_base_params["variable_cost"],
        "ramp_up": 0.0,
        "ramp_down": None,
        "min_up_time": None,
        "min_down_time": None,
        "min_power": 0.0,
        "startup_cost": 0.0,
        "shutdown_cost": 0.0,
    }
    gen = Generator(**base_params)
    assert gen.ramp_up == 0.0


def test_generator_ramp_down_can_be_zero(
    generator_base_params: GeneratorBaseParams,
) -> None:
    base_params: GeneratorParams = {
        "name": generator_base_params["name"],
        "nominal_power": generator_base_params["nominal_power"],
        "variable_cost": generator_base_params["variable_cost"],
        "ramp_up": None,
        "ramp_down": 0.0,
        "min_up_time": None,
        "min_down_time": None,
        "min_power": 0.0,
        "startup_cost": 0.0,
        "shutdown_cost": 0.0,
    }
    gen = Generator(**base_params)
    assert gen.ramp_down == 0.0


def test_generator_min_power_defaults_to_zero(
    generator_base_params: GeneratorBaseParams,
) -> None:
    base_params: GeneratorParams = {
        "name": generator_base_params["name"],
        "nominal_power": generator_base_params["nominal_power"],
        "variable_cost": generator_base_params["variable_cost"],
        "ramp_up": None,
        "ramp_down": None,
        "min_up_time": None,
        "min_down_time": None,
        "min_power": 0.0,
        "startup_cost": 0.0,
        "shutdown_cost": 0.0,
    }
    gen = Generator(**base_params)
    assert gen.min_power == 0.0


def test_generator_min_up_and_down_times_default_to_none(generator_base_params: GeneratorBaseParams) -> None:
    gen = Generator(**generator_base_params)

    assert gen.min_up_time is None
    assert gen.min_down_time is None


@pytest.mark.parametrize(
    ("timestep", "min_up_time"),
    [(timedelta(hours=1), MIN_UP_TIME), (timedelta(minutes=15), timedelta(minutes=45))],
    ids=["hourly", "quarter_hourly"],
)
def test_generator_validate_horizon_accepts_whole_step_min_times(
    generator_base_params: GeneratorBaseParams,
    timestep: timedelta,
    min_up_time: timedelta,
) -> None:
    gen = Generator(**generator_base_params, min_up_time=min_up_time, min_down_time=min_up_time)

    gen.validate_horizon(Horizon(timestep=timestep, number_of_steps=NUMBER_OF_STEPS))


@pytest.mark.parametrize("field", ["min_up_time", "min_down_time"])
def test_generator_validate_horizon_rejects_min_time_not_a_whole_number_of_steps(
    generator_base_params: GeneratorBaseParams,
    field: str,
) -> None:
    gen = Generator.model_validate({**generator_base_params, field: timedelta(minutes=90)})

    with pytest.raises(
        OdysValidationError,
        match=rf"Generator 'test_generator' has {field}=1:30:00, which is not a whole number of timesteps \(1:00:00\)",
    ):
        gen.validate_horizon(Horizon(timestep=timedelta(hours=1), number_of_steps=NUMBER_OF_STEPS))


@pytest.mark.parametrize("field", ["min_up_time", "min_down_time"])
def test_generator_rejects_a_number_of_steps_as_min_time(
    generator_base_params: GeneratorBaseParams,
    field: str,
) -> None:
    """Minimum times used to be step counts; a bare number is rejected instead of being read as seconds."""
    with pytest.raises(ValidationError, match="Input should be a valid timedelta"):
        Generator.model_validate({**generator_base_params, field: 3})
