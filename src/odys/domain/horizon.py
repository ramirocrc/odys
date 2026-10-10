"""The time grid of one optimization and the conditions an entity faces on it."""

from datetime import timedelta

from pydantic import BaseModel, ConfigDict, Field


class Horizon(BaseModel):
    """The time grid of one optimization: the step length and the number of steps."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    timestep: timedelta = Field(gt=timedelta(0), description="Duration of one optimization step.")
    number_of_steps: int = Field(strict=True, ge=1, description="Number of optimization steps.")

    @property
    def hours_per_step(self) -> float:
        """Return the length of one step in hours."""
        return self.timestep / timedelta(hours=1)


class OperatingConditions(BaseModel):
    """What one entity faces in one scenario: the horizon and its profile values, if it has a profile."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    horizon: Horizon
    profile_values: tuple[float, ...] | None = None
