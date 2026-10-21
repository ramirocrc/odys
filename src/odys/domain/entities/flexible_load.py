"""Flexible load asset implementation.

This module provides the FlexibleLoad class for modeling adjustable energy consumption
in energy system optimization problems.
"""

from typing import Self

from pydantic import Field, model_validator

from odys.domain.entities.base import Asset
from odys.domain.entities.commitment import Commitment
from odys.domain.exceptions import OdysValidationError
from odys.domain.horizon import Horizon, OperatingConditions


class FlexibleLoad(Asset):
    """Represents a flexible load asset in the energy system.

    A flexible load is demand the optimizer may set anywhere within a range
    at every step: a process that can run harder when power is cheap and
    slow down when it is expensive. Each scenario gives the range as a
    `FlexibleLoadProfile` (a lower and an upper bound per step).

    The decision depends on the relationship between the
    value_of_consumption (economic value of consuming electricity) and the
    marginal cost of supply. The marginal cost is determined implicitly by
    the power balance constraint: consuming more means procuring more
    energy from the cheapest available source (generators or markets), and
    consuming less frees up that supply for other uses (e.g., selling to
    markets).

    When value_of_consumption exceeds the marginal supply cost, the load
    runs at its upper bound. When the marginal supply cost exceeds
    value_of_consumption, it runs at its lower bound.

    The optional min_load and max_load are the load's physical limits while it
    runs: every scenario's range must lie within them.

    An industrial process may also change only gradually (ramp_up, ramp_down)
    and be switched off (commitment). Without a commitment the load always runs
    within its range. With one, it is either off, consuming 0 MW, or running
    within its range, and its commitment sets the minimum up and down times
    and the cost of each start and stop. The ramp limits apply between two
    running steps: a start can land anywhere in the range, and a stop drops
    to 0.
    """

    min_load: float | None = Field(
        default=None,
        strict=True,
        ge=0,
        description="Least the load can consume while running, in MW. Every lower bound must be at least this.",
    )

    max_load: float | None = Field(
        default=None,
        strict=True,
        gt=0,
        description="Most the load can consume while running, in MW. Every upper bound must be at most this.",
    )

    value_of_consumption: float = Field(
        strict=True,
        ge=0,
        description="Economic value of consuming electricity in currency per MWh.",
    )

    ramp_up: float | None = Field(
        default=None,
        strict=True,
        ge=0,
        description="Largest increase in consumption between two running steps, in MW per hour. None means no limit.",
    )

    ramp_down: float | None = Field(
        default=None,
        strict=True,
        ge=0,
        description="Largest decrease in consumption between two running steps, in MW per hour. None means no limit.",
    )

    commitment: Commitment | None = Field(
        default=None,
        description=(
            "How the load is switched on and off. None means it always runs within its range; "
            "with a commitment it can be off, consuming 0 MW."
        ),
    )

    @model_validator(mode="after")
    def _validate_min_load_not_above_max_load(self) -> Self:
        if self.min_load is not None and self.max_load is not None and self.min_load > self.max_load:
            msg = f"min_load ({self.min_load}) must be ≤ max_load ({self.max_load})."
            raise OdysValidationError(msg)
        return self

    def min_demand(self, conditions: OperatingConditions) -> tuple[float, ...]:
        """Return the lower bound of the load's range when it has a profile and can't be switched off, in MW."""
        if conditions.profile_values is not None and self.commitment is None:
            return conditions.profile_values
        return super().min_demand(conditions)

    def validate_horizon(self, horizon: Horizon) -> None:
        """Check that the minimum up and down times of the load's commitment span a whole number of timesteps.

        Args:
            horizon: The time grid of the optimization.

        Raises:
            OdysValidationError: If a minimum time is not a whole number of timesteps.
        """
        if self.commitment is not None:
            self.commitment.validate_horizon(horizon, f"Flexible load '{self.name}'")
