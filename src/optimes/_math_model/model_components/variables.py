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
    BATTERY_CHARGE = "battery_charge"
    BATTERY_DISCHARGE = "battery_discharge"
    BATTERY_CHARGE_MODE = "battery_charge_mode"
