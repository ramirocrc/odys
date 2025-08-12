"""Power generator asset implementation.

This module provides the PowerGenerator class for modeling electrical generators
in energy system optimization problems.
"""

from datetime import timedelta
from typing import Annotated

from pydantic import Field

from optimes.energy_system_models.assets.base import EnergyAsset


class PowerGenerator(EnergyAsset, frozen=True):
    """Represents a power generator in the energy system.

    This class models generators with various operational constraints
    including nominal power, variable costs, ramp rates, and startup/shutdown costs.
    """

    nominal_power: Annotated[
        float,
        Field(
            strict=True,
            gt=0,
            description="Nominal power of the generator in MW",
        ),
    ]

    variable_cost: Annotated[
        float,
        Field(
            strict=True,
            gt=0,
            description="Variable cost of the generator in currency per MWh",
        ),
    ]

    ramp_up: Annotated[
        float | None,
        Field(
            strict=True,
            gt=0,
            description="Ramp-up rate of the generator in MW per hour",
        ),
    ] = None

    ramp_down: Annotated[
        float | None,
        Field(
            strict=True,
            gt=0,
            description="Ramp-down rate of the generator in MW per hour",
        ),
    ] = None

    min_up_time: Annotated[
        timedelta | None,
        Field(
            ge=timedelta(0),
            description="Minimum up time",
        ),
    ] = None

    min_down_time: Annotated[
        timedelta | None,
        Field(
            ge=timedelta(0),
            description="Minimum down time",
        ),
    ] = None

    startup_cost: Annotated[
        float | None,
        Field(
            strict=True,
            ge=0,
            description="Startup cost of the generator, in currency per MWh",
        ),
    ] = None

    shutdown_cost: Annotated[
        float | None,
        Field(
            strict=True,
            ge=0,
            description="Shutdown cost of the generator, in currency per MWh",
        ),
    ] = None

    emission_factor: Annotated[
        float | None,
        Field(
            strict=True,
            ge=0,
            description="Emission factor of the generator in kg CO2 per MWh",
        ),
    ] = None
