"""Tests for the optimization horizon."""

from datetime import timedelta

import pytest
from pydantic import ValidationError

from odys.domain.exceptions import OdysError
from odys.domain.horizon import Horizon

NUMBER_OF_STEPS = 4
QUARTER_HOUR = 0.25
STEPS_IN_THREE_QUARTERS = 3


def test_horizon_hours_per_step_converts_the_timestep() -> None:
    horizon = Horizon(timestep=timedelta(minutes=15), number_of_steps=NUMBER_OF_STEPS)

    assert horizon.hours_per_step == pytest.approx(QUARTER_HOUR)


@pytest.mark.parametrize("timestep", [timedelta(0), timedelta(hours=-1)], ids=["zero", "negative"])
def test_horizon_non_positive_timestep_is_rejected(timestep: timedelta) -> None:
    with pytest.raises(ValidationError, match=r"timestep\n  Input should be greater than 0 seconds"):
        Horizon(timestep=timestep, number_of_steps=NUMBER_OF_STEPS)


def test_horizon_without_steps_is_rejected() -> None:
    with pytest.raises(ValidationError, match="greater than or equal to 1"):
        Horizon.model_validate({"timestep": timedelta(hours=1), "number_of_steps": 0})


def test_horizon_is_frozen() -> None:
    horizon = Horizon(timestep=timedelta(hours=1), number_of_steps=NUMBER_OF_STEPS)
    frozen_field = "number_of_steps"

    with pytest.raises(ValidationError, match="Instance is frozen"):
        setattr(horizon, frozen_field, 1)


@pytest.mark.parametrize(
    ("duration", "is_whole"),
    [(timedelta(minutes=45), True), (timedelta(minutes=50), False), (timedelta(hours=2), True)],
    ids=["three_steps", "partial_step", "eight_steps"],
)
def test_horizon_is_whole_steps_checks_the_duration_against_the_timestep(
    duration: timedelta,
    *,
    is_whole: bool,
) -> None:
    horizon = Horizon(timestep=timedelta(minutes=15), number_of_steps=NUMBER_OF_STEPS)

    assert horizon.is_whole_steps(duration) is is_whole


def test_horizon_steps_in_counts_the_steps_of_a_duration() -> None:
    horizon = Horizon(timestep=timedelta(minutes=15), number_of_steps=NUMBER_OF_STEPS)

    assert horizon.steps_in(timedelta(minutes=45)) == STEPS_IN_THREE_QUARTERS


def test_horizon_steps_in_rejects_a_partial_step() -> None:
    horizon = Horizon(timestep=timedelta(minutes=15), number_of_steps=NUMBER_OF_STEPS)

    with pytest.raises(OdysError, match=r"0:50:00 is not a whole number of timesteps \(0:15:00\)"):
        horizon.steps_in(timedelta(minutes=50))
