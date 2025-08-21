"""Module to represent power units."""

from enum import Enum


class PowerUnit(Enum):
    """Power unit."""

    Watt = "W"
    KiloWatt = "kW"
    MegaWatt = "MW"
