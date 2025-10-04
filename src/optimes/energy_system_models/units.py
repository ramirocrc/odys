"""Module to represent power units."""

from enum import StrEnum


class PowerUnit(StrEnum):
    """Power unit."""

    Watt = "W"
    KiloWatt = "kW"
    MegaWatt = "MW"
