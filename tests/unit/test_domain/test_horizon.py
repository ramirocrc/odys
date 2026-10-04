"""Tests for the optimization horizon."""

from datetime import timedelta

import pytest
from pydantic import ValidationError

from odys.domain.horizon import Horizon

NUMBER_OF_STEPS = 4
QUARTER_HOUR = 0.25


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
