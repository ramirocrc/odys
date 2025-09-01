"""Variable definitions for energy system optimization models.

This module defines variable names and types used in energy system
optimization models.
"""

from enum import Enum, unique


@unique
class EnergyModelVariableName(Enum):
    """Enumeration of variable names used in the energy model."""

    GENERATOR_POWER = "generator_power"
    BATTERY_SOC = "battery_soc"
    BATTERY_POWER_IN = "battery_power_in"
    BATTERY_POWER_OUT = "battery_power_out"
    BATTERY_CHARGE_MODE = "battery_charge_mode"
