from enum import Enum, unique


@unique
class EnergyModelConstraintName(Enum):
    """Enumeration of constraint names used in the energy model."""

    POWER_BALANCE = "power_balance"
    GENERATOR_LIMIT = "generator_max_power"
    BATTERY_CHARGE_LIMIT = "battery_max_charge"
    BATTERY_DISCHARGE_LIMIT = "battery_max_discharge"
    BATTERY_SOC_DYNAMICS = "const_battery_soc_dynamics"
    BATTERY_SOC_BOUNDS = "const_battery_soc_bounds"
    BATTERY_SOC_START = "const_battery_soc_start"
    BATTERY_SOC_END = "const_battery_soc_end"
