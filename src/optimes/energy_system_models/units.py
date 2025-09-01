"""Module to represent power units."""

from enum import Enum


class PowerUnit(str, Enum):
    """Power unit."""

    Watt = "W"
    KiloWatt = "kW"
    MegaWatt = "MW"

    def __str__(self) -> str:  # noqa: D105
        return self.value

    def __repr__(self) -> str:  # noqa: D105
        return self.value
