"""Power generator asset implementation.

This module provides the PowerGenerator class for modeling electrical generators
in energy system optimization problems.
"""

from pydantic import Field

from odis.energy_system_models.assets.base import EnergyAsset


class PowerGenerator(EnergyAsset, frozen=True):
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
        gt=0,
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

    min_up_time: int = Field(
        default=1,
        strict=True,
        ge=1,
        description="Minimum up time",
    )

    min_down_time: int = Field(
        default=1,
        strict=True,
        ge=1,
        description="Minimum down time",
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
        description="Startup cost of the generator, in currency per MWh.",
    )

    shutdown_cost: float | None = Field(
        default=None,
        strict=True,
        ge=0,
        description="Shutdown cost of the generator, in currency per MWh",
    )
