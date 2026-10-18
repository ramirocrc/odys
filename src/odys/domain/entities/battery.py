"""Battery value object.

This module provides the Battery class: the physics of storing electrical
energy, shared by assets that have a battery (battery storage, electric
vehicles).
"""

from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from odys.domain.exceptions import OdysValidationError


class Battery(BaseModel):
    """Physics of a battery: capacity, power limits, efficiencies, and state of charge limits.

    A battery has no name and no identity of its own. It is a value object that
    an asset (`BatteryStorage`, `ElectricVehicle`) owns. Its state of charge at
    the start and end of an optimization belongs to that run, not to the battery,
    and is given as an initial or final condition of the `EnergySystem`.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    capacity: float = Field(
        strict=True,
        gt=0,
        description="Storage capacity in MWh.",
    )
    max_charge_power: float = Field(
        strict=True,
        gt=0,
        description="Maximum charging power in MW.",
    )
    max_discharge_power: float = Field(
        strict=True,
        ge=0,
        description="Maximum discharging power in MW. 0 = charge-only.",
    )
    efficiency_charging: float = Field(
        default=1,
        strict=True,
        gt=0,
        le=1,
        description="Charging efficiency (0-1).",
    )
    efficiency_discharging: float = Field(
        default=1,
        strict=True,
        gt=0,
        le=1,
        description="Discharging efficiency (0-1).",
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
    degradation_cost: float = Field(
        default=0.0,
        strict=True,
        ge=0,
        description="Degradation cost, in currency per MWh cycled.",
    )
    self_discharge_rate: float = Field(
        default=0.0,
        strict=True,
        ge=0,
        le=1,
        description="Self-discharge rate (0-1) per hour.",
    )

    @model_validator(mode="after")
    def _validate_soc_min_less_than_max(self) -> Self:
        if self.soc_min >= self.soc_max:
            msg = f"soc_min ({self.soc_min}) must be < soc_max ({self.soc_max})."
            raise OdysValidationError(msg)
        return self
