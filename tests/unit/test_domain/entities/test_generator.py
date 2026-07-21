from typing import Any, TypedDict, cast

import pytest
from pydantic import ValidationError

from odys.domain.entities.generator import Generator


class GeneratorBaseParams(TypedDict):
    name: str
    nominal_power: float
    variable_cost: float


class GeneratorParams(GeneratorBaseParams, total=False):
    ramp_up: float | None
    ramp_down: float | None
    min_up_time: int
    min_down_time: int
    min_power: float
    startup_cost: float
    shutdown_cost: float


NOMINAL_POWER = 100.0
VARIABLE_COST = 50.0
RAMP_UP = 50.0
RAMP_DOWN = 40.0
MIN_UP_TIME = 3
MIN_DOWN_TIME = 2
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
        ("min_up_time", 0, "Input should be greater than or equal to 1"),
        ("min_down_time", 0, "Input should be greater than or equal to 1"),
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
        "min_up_time": 1,
        "min_down_time": 1,
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
    assert gen.min_up_time == 1
    assert gen.min_down_time == 1
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
        "min_up_time": 1,
        "min_down_time": 1,
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
        "min_up_time": 1,
        "min_down_time": 1,
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
        "min_up_time": 1,
        "min_down_time": 1,
        "min_power": 0.0,
        "startup_cost": 0.0,
        "shutdown_cost": 0.0,
    }
    gen = Generator(**base_params)
    assert gen.min_power == 0.0
