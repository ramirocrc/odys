"""The time grid of one optimization and the conditions an entity faces on it."""

from datetime import timedelta

from pydantic import BaseModel, ConfigDict, Field

from odys.domain.exceptions import OdysError


class Horizon(BaseModel):
    """The time grid of one optimization: the step length and the number of steps."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    timestep: timedelta = Field(gt=timedelta(0), description="Duration of one optimization step.")
    number_of_steps: int = Field(strict=True, ge=1, description="Number of optimization steps.")

    @property
    def hours_per_step(self) -> float:
        """Return the length of one step in hours."""
        return self.timestep / timedelta(hours=1)

    def is_whole_steps(self, duration: timedelta) -> bool:
        """Return whether `duration` spans a whole number of steps."""
        return not duration % self.timestep

    def steps_in(self, duration: timedelta) -> int:
        """Return the number of steps `duration` spans.

        Args:
            duration: A whole number of steps, as checked by `is_whole_steps`.

        Returns:
            The number of steps.

        Raises:
            OdysError: If `duration` is not a whole number of steps.
        """
        if not self.is_whole_steps(duration):
            msg = f"{duration} is not a whole number of timesteps ({self.timestep})."
            raise OdysError(msg)
        return duration // self.timestep


class OperatingConditions(BaseModel):
    """What one entity faces in one scenario: the horizon and its profile values, if it has a profile."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    horizon: Horizon
    profile_values: tuple[float, ...] | None = None
