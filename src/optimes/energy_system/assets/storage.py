from typing import Annotated, Self

from pydantic import Field, model_validator

from optimes.energy_system.assets.base import EnergyAsset


class Battery(EnergyAsset, frozen=True):
    """Represents a battery storage system in the energy system.

    This class models batteries with various operational constraints
    including capacity, power limits, efficiency, state of charge,
    and degradation characteristics.
    """

    capacity: Annotated[
        float,
        Field(
            strict=True,
            gt=0,
            description="Battery capacity in MWh",
        ),
    ]
    max_power: Annotated[
        float,
        Field(
            strict=True,
            gt=0,
            description="Maximum power in MW",
        ),
    ]
    efficiency_charging: Annotated[
        float,
        Field(
            strict=True,
            gt=0,
            le=1,
            description="Charging efficiency (0-1)",
        ),
    ]
    efficiency_discharging: Annotated[
        float,
        Field(
            strict=True,
            gt=0,
            le=1,
            description="Discharging efficiency (0-1)",
        ),
    ]
    soc_initial: Annotated[
        float,
        Field(
            strict=True,
            ge=0,
            description="Initial state of charge in MWh",
        ),
    ]
    soc_terminal: Annotated[
        float | None,
        Field(
            strict=True,
            ge=0,
            description="Final state of charge in MWh",
        ),
    ] = None
    soc_min: Annotated[
        float | None,
        Field(
            strict=True,
            ge=0,
            le=1,
            description="Minimum state of charge (0-1)",
        ),
    ] = None
    soc_max: Annotated[
        float | None,
        Field(
            strict=True,
            ge=0,
            le=1,
            description="Maximum state of charge (0-1)",
        ),
    ] = None
    degradation_cost: Annotated[
        float | None,
        Field(
            strict=True,
            ge=0,
            description="Degradation cost, in currency per MWh cycled",
        ),
    ] = None
    self_discharge_rate: Annotated[
        float | None,
        Field(
            strict=True,
            ge=0,
            le=1,
            description="Self-discharge rate (0-1) per hour",
        ),
    ] = None

    @model_validator(mode="after")
    def validate_soc_values_remain_within_capacity(self) -> Self:
        """Validate that all SOC values are within the battery capacity.

        This validator ensures that initial SOC, terminal SOC, and
        SOC bounds do not exceed the battery's capacity.

        Returns:
            Self if validation passes.

        Raises:
            ValueError: If any SOC value exceeds the battery capacity.
        """
        limits = {
            "soc_initial": self.soc_initial,
            "soc_terminal": self.soc_terminal,
            "soc_min": self.soc_min,
            "soc_max": self.soc_max,
        }

        for name, battery_soc in limits.items():
            if battery_soc is not None and battery_soc > self.capacity:
                msg = f"{name} ({battery_soc}) must be less than the battery capacity ({self.capacity})."
                raise ValueError(msg)

        return self

    @model_validator(mode="after")
    def validate_soc_initial_and_terminal(self) -> Self:
        """Validate that initial and terminal SOC values respect min/max bounds.

        This validator ensures that initial and terminal SOC values
        are within the specified SOC bounds if they are set.

        Returns:
            Self if validation passes.

        Raises:
            ValueError: If SOC values are outside the specified bounds.
        """
        for name in ("soc_initial", "soc_terminal"):
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
