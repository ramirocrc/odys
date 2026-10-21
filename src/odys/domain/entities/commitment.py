"""Commitment value object.

This module provides the Commitment class: how an asset is switched on and
off, shared by assets that can be off (generators, switchable flexible loads).
"""

from datetime import timedelta

from pydantic import BaseModel, ConfigDict, Field

from odys.domain.exceptions import OdysValidationError
from odys.domain.horizon import Horizon


class Commitment(BaseModel):
    """How an asset is switched on and off: minimum up and down times, and start-up and shut-down costs.

    A commitment has no name and no identity of its own. It is a value object
    that an asset (`Generator`, `FlexibleLoad`) owns. `Commitment()` lets the
    asset switch freely, with no minimum times and no costs.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    min_up_time: timedelta | None = Field(
        default=None,
        strict=True,
        gt=timedelta(0),
        description="Minimum time the asset stays on once started. None means no minimum.",
    )

    min_down_time: timedelta | None = Field(
        default=None,
        strict=True,
        gt=timedelta(0),
        description="Minimum time the asset stays off once stopped. None means no minimum.",
    )

    startup_cost: float = Field(
        default=0.0,
        strict=True,
        ge=0,
        description="Cost of starting the asset, in currency per startup.",
    )

    shutdown_cost: float = Field(
        default=0.0,
        strict=True,
        ge=0,
        description="Cost of stopping the asset, in currency per shutdown.",
    )

    def validate_horizon(self, horizon: Horizon, owner: str) -> None:
        """Check that the minimum up and down times span a whole number of timesteps.

        Args:
            horizon: The time grid of the optimization.
            owner: The asset this commitment belongs to, as named in the error, such as "Generator 'ccgt'".

        Raises:
            OdysValidationError: If a minimum time is not a whole number of timesteps.
        """
        for field, duration in (("min_up_time", self.min_up_time), ("min_down_time", self.min_down_time)):
            if duration is not None and not horizon.is_whole_steps(duration):
                msg = f"{owner} has {field}={duration}, which is not a whole number of timesteps ({horizon.timestep})."
                raise OdysValidationError(msg)

    def time_coupled_fields(self) -> tuple[str, ...]:
        """Return the names of the set fields that link one timestep to the next.

        Returns:
            The minimum times that are set and the costs above zero, in field order.
        """
        is_set = {
            "min_up_time": self.min_up_time is not None,
            "min_down_time": self.min_down_time is not None,
            "startup_cost": self.startup_cost > 0,
            "shutdown_cost": self.shutdown_cost > 0,
        }
        return tuple(field for field, field_is_set in is_set.items() if field_is_set)
