from enum import Enum, unique


@unique
class EnergyModelConstraintName(Enum):
    """Enumeration of constraint names used in the energy model."""

    POWER_BALANCE = "const_power_balance"
    GENERATOR_LIMIT = "const_generator_limit"
    BATTERY_CHARGE_LIMIT = "const_battery_charge_limit"
    BATTERY_DISCHARGE_LIMIT = "const_battery_discharge_limit"
    BATTERY_SOC_DYNAMICS = "const_battery_soc_dynamics"
    BATTERY_SOC_BOUNDS = "const_battery_soc_bounds"
    BATTERY_SOC_START = "const_battery_soc_start"
    BATTERY_SOC_END = "const_battery_soc_end"
