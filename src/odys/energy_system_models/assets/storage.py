"""Energy storage asset implementation.

This module provides the Battery class for modeling energy storage devices
in energy system optimization problems.
"""

from typing import Self

from pydantic import Field, model_validator

from odys.energy_system_models.assets.base import EnergyAsset


class Battery(EnergyAsset, frozen=True):
    """Represents a battery storage system in the energy system.

    This class models batteries with various operational constraints
    including capacity, power limits, efficiency, state of charge,
    and degradation characteristics.
    """

    capacity: float = Field(
        strict=True,
        gt=0,
        description="Battery capacity in MWh.",
    )
    max_power: float = Field(
        strict=True,
        gt=0,
        description="Maximum power in MW.",
    )
    efficiency_charging: float = Field(
        strict=True,
        gt=0,
        le=1,
        description="Charging efficiency (0-1).",
    )
    efficiency_discharging: float = Field(
        strict=True,
        gt=0,
        le=1,
        description="Discharging efficiency (0-1).",
    )
    soc_start: float = Field(
        strict=True,
        ge=0,
        le=1,
        description="Initial state of charge as a fraction of capacity (0-1).",
    )
    soc_end: float | None = Field(
        default=None,
        strict=True,
        ge=0,
        le=1,
        description="Final state of charge as a fraction of capacity (0-1).",
    )
    soc_min: float = Field(
        default=0,
        strict=True,
        ge=0,
        le=1,
        description="Minimum state of charge as a fraction of capacity (0-1).",
    )
    soc_max: float = Field(
        default=1,
        strict=True,
        ge=0,
        le=1,
        description="Maximum state of charge as a fraction of capacity (0-1).",
    )
    degradation_cost: float | None = Field(
        default=None,
        strict=True,
        ge=0,
        description="Degradation cost, in currency per MWh cycled.",
    )
    self_discharge_rate: float | None = Field(
        default=None,
        strict=True,
        ge=0,
        le=1,
        description="Self-discharge rate (0-1) per hour.",
    )

    @model_validator(mode="after")
    def _validate_soc_start_and_terminal(self) -> Self:
        for name in ("soc_start", "soc_end"):
            battery_soc = getattr(self, name)
            if battery_soc is None:
                continue

            if self.soc_min is not None and battery_soc < self.soc_min:
                msg = f"{name} ({battery_soc}) must be ≥ soc_min ({self.soc_min})."
                raise ValueError(msg)
            if self.soc_max is not None and battery_soc > self.soc_max:
                msg = f"{name} ({battery_soc}) must be ≤ soc_max ({self.soc_max})."
                raise ValueError(msg)

        return self

    @model_validator(mode="after")
    def _validate_soc_min_less_than_max(self) -> Self:
        if self.soc_min is None or self.soc_max is None:
            return self
        if self.soc_min >= self.soc_max:
            msg = f"soc_min ({self.soc_min}) must be < soc_max ({self.soc_max})."
            raise ValueError(msg)
        return self
