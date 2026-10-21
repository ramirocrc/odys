from datetime import timedelta

import pytest
from pydantic import ValidationError

from odys.domain.entities.commitment import Commitment
from odys.domain.exceptions import OdysValidationError
from odys.domain.horizon import Horizon

MIN_UP_TIME = timedelta(hours=3)
MIN_DOWN_TIME = timedelta(hours=2)
STARTUP_COST = 100.0
SHUTDOWN_COST = 50.0
NUMBER_OF_STEPS = 24
OWNER = "Generator 'ccgt'"


def test_commitment_defaults_switch_freely() -> None:
    commitment = Commitment()

    assert commitment.min_up_time is None
    assert commitment.min_down_time is None
    assert commitment.startup_cost == 0.0
    assert commitment.shutdown_cost == 0.0


def test_commitment_creation_with_all_fields() -> None:
    commitment = Commitment(
        min_up_time=MIN_UP_TIME,
        min_down_time=MIN_DOWN_TIME,
        startup_cost=STARTUP_COST,
        shutdown_cost=SHUTDOWN_COST,
    )

    assert commitment.min_up_time == MIN_UP_TIME
    assert commitment.min_down_time == MIN_DOWN_TIME
    assert commitment.startup_cost == STARTUP_COST
    assert commitment.shutdown_cost == SHUTDOWN_COST


@pytest.mark.parametrize(
    ("field", "invalid_value", "expected_match"),
    [
        ("min_up_time", timedelta(0), "Input should be greater than 0"),
        ("min_down_time", timedelta(hours=-1), "Input should be greater than 0"),
        ("startup_cost", -10.0, "Input should be greater than or equal to 0"),
        ("shutdown_cost", -10.0, "Input should be greater than or equal to 0"),
    ],
)
def test_commitment_rejects_a_field_out_of_range(field: str, invalid_value: object, expected_match: str) -> None:
    with pytest.raises(ValidationError, match=expected_match):
        Commitment.model_validate({field: invalid_value})


@pytest.mark.parametrize("field", ["min_up_time", "min_down_time"])
def test_commitment_rejects_a_number_of_steps_as_min_time(field: str) -> None:
    """Minimum times used to be step counts; a bare number is rejected instead of being read as seconds."""
    with pytest.raises(ValidationError, match="Input should be a valid timedelta"):
        Commitment.model_validate({field: 3})


def test_commitment_is_frozen() -> None:
    commitment = Commitment()
    frozen_field = "startup_cost"

    with pytest.raises(ValidationError, match="Instance is frozen"):
        setattr(commitment, frozen_field, STARTUP_COST)


@pytest.mark.parametrize(
    ("timestep", "min_time"),
    [(timedelta(hours=1), MIN_UP_TIME), (timedelta(minutes=15), timedelta(minutes=45))],
    ids=["hourly", "quarter_hourly"],
)
def test_commitment_validate_horizon_accepts_whole_step_min_times(timestep: timedelta, min_time: timedelta) -> None:
    commitment = Commitment(min_up_time=min_time, min_down_time=min_time)

    commitment.validate_horizon(Horizon(timestep=timestep, number_of_steps=NUMBER_OF_STEPS), OWNER)


@pytest.mark.parametrize("field", ["min_up_time", "min_down_time"])
def test_commitment_validate_horizon_rejects_min_time_not_a_whole_number_of_steps(field: str) -> None:
    commitment = Commitment.model_validate({field: timedelta(minutes=90)})

    with pytest.raises(
        OdysValidationError,
        match=rf"Generator 'ccgt' has {field}=1:30:00, which is not a whole number of timesteps \(1:00:00\)",
    ):
        commitment.validate_horizon(Horizon(timestep=timedelta(hours=1), number_of_steps=NUMBER_OF_STEPS), OWNER)


@pytest.mark.parametrize(
    ("commitment", "expected"),
    [
        (Commitment(), ()),
        (Commitment(min_down_time=MIN_DOWN_TIME, shutdown_cost=SHUTDOWN_COST), ("min_down_time", "shutdown_cost")),
        (
            Commitment(
                min_up_time=MIN_UP_TIME,
                min_down_time=MIN_DOWN_TIME,
                startup_cost=STARTUP_COST,
                shutdown_cost=SHUTDOWN_COST,
            ),
            ("min_up_time", "min_down_time", "startup_cost", "shutdown_cost"),
        ),
    ],
    ids=["none", "some", "all"],
)
def test_commitment_time_coupled_fields_are_the_set_fields_in_order(
    commitment: Commitment,
    expected: tuple[str, ...],
) -> None:
    assert commitment.time_coupled_fields() == expected
