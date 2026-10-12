"""Generator asset implementation.

This module provides the Generator class for modeling electrical generators
in energy system optimization problems.
"""

from datetime import timedelta

from pydantic import Field

from odys.domain.entities.base import Asset
from odys.domain.exceptions import OdysValidationError
from odys.domain.horizon import Horizon, OperatingConditions


class Generator(Asset):
    """Represents a power generator in the energy system.

    This class models generators with various operational constraints
    including nominal power, variable costs, ramp rates, and startup/shutdown costs.
    """

    nominal_power: float = Field(
        strict=True,
        gt=0,
        description="Nominal power of the generator in MW.",
    )

    variable_cost: float = Field(
        strict=True,
        ge=0,
        description="Variable cost of the generator in currency per MWh.",
    )

    ramp_up: float | None = Field(
        default=None,
        strict=True,
        ge=0,
        description="Ramp-up rate of the generator in MW per hour",
    )

    ramp_down: float | None = Field(
        default=None,
        strict=True,
        ge=0,
        description="Ramp-down rate of the generator in MW per hour",
    )

    min_up_time: timedelta | None = Field(
        default=None,
        strict=True,
        gt=timedelta(0),
        description="Minimum time the generator stays on once started. None means no minimum.",
    )

    min_down_time: timedelta | None = Field(
        default=None,
        strict=True,
        gt=timedelta(0),
        description="Minimum time the generator stays off once stopped. None means no minimum.",
    )

    min_power: float = Field(
        default=0.0,
        strict=True,
        ge=0,
        description="Minimum power output",
    )

    startup_cost: float = Field(
        default=0.0,
        strict=True,
        ge=0,
        description="Startup cost of the generator, in currency per startup.",
    )

    shutdown_cost: float = Field(
        default=0.0,
        strict=True,
        ge=0,
        description="Shutdown cost of the generator, in currency per shutdown.",
    )

    def max_supply(self, conditions: OperatingConditions) -> tuple[float, ...]:
        """Return the available capacity profile if the scenario has one, else the nominal power, in MW."""
        if conditions.profile_values is not None:
            return conditions.profile_values
        return (self.nominal_power,) * conditions.horizon.number_of_steps

    def validate_horizon(self, horizon: Horizon) -> None:
        """Check that the minimum up and down times span a whole number of timesteps.

        Args:
            horizon: The time grid of the optimization.

        Raises:
            OdysValidationError: If a minimum time is not a whole number of timesteps.
        """
        for field, duration in (("min_up_time", self.min_up_time), ("min_down_time", self.min_down_time)):
            if duration is not None and not horizon.is_whole_steps(duration):
                msg = (
                    f"Generator '{self.name}' has {field}={duration}, "
                    f"which is not a whole number of timesteps ({horizon.timestep})."
                )
                raise OdysValidationError(msg)
