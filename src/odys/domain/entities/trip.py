"""Trip entity for electric vehicle scheduling.

This module provides the Trip class for modeling vehicle trips that consume
energy and make the vehicle unavailable for charging.
"""

from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from odys.domain.exceptions import OdysValidationError


class Trip(BaseModel):
    """Represents a vehicle trip that consumes energy and makes the vehicle unavailable.

    Trips define when an EV is driving (unavailable for charging) and how much
    energy is consumed. They also specify minimum SoC requirements at departure.

    Note: energy_consumption represents the battery-side energy consumed during the trip.
    This is the energy that must be provided by the battery, accounting for all losses
    in the drivetrain. Fleet managers can estimate this from vehicle telemetry (kWh used)
    or calculate from distance x vehicle efficiency.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str
    start_time: int = Field(ge=0, description="Timestep index when trip starts.")
    end_time: int = Field(ge=0, description="Timestep index when trip ends.")
    energy_consumption: float = Field(
        gt=0,
        description="Battery-side energy consumed during trip in MWh. This is what the battery provides.",
    )
    min_soc_at_departure: float = Field(
        default=0.0,
        ge=0,
        le=1,
        description="Minimum SoC required at departure (start_time), before trip energy is consumed.",
    )

    @model_validator(mode="after")
    def _validate_time_window(self) -> Self:
        if self.end_time <= self.start_time:
            msg = f"end_time ({self.end_time}) must be > start_time ({self.start_time})."
            raise OdysValidationError(msg)
        return self
