"""Variable definitions for energy system optimization models.

This module defines variable names and types used in energy system
optimization models.
"""

from enum import Enum, unique


@unique
class EnergyModelVariableName(Enum):
    """Enumeration of variable names used in the energy model."""

    GENERATOR_POWER = "var_generator_power"
    BATTERY_SOC = "var_battery_soc"
    BATTERY_CHARGE = "var_battery_charge"
    BATTERY_DISCHARGE = "var_battery_discharge"
    BATTERY_CHARGE_MODE = "var_battery_charge_mode"
