"""Generator asset implementation.

This module provides the Generator class for modeling electrical generators
in energy system optimization problems.
"""

from pydantic import Field

from odys.domain.entities.base import Asset
from odys.domain.entities.commitment import Commitment
from odys.domain.horizon import Horizon, OperatingConditions


class Generator(Asset):
    """Represents a power generator in the energy system.

    This class models generators with various operational constraints
    including nominal power, variable costs and ramp rates. How it is switched
    on and off (minimum up and down times, startup and shutdown costs) is its
    `Commitment`.
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

    min_power: float = Field(
        default=0.0,
        strict=True,
        ge=0,
        description="Minimum power output",
    )

    commitment: Commitment = Field(
        default_factory=Commitment,
        description="How the generator is switched on and off: minimum up and down times, startup and shutdown costs.",
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
        self.commitment.validate_horizon(horizon, f"Generator '{self.name}'")
