from enum import Enum, unique


@unique
class EnergyModelConstraintName(Enum):
    """Enumeration of constraint names used in the energy model."""

    POWER_BALANCE = "power_balance_constraint"
    GENERATOR_LIMIT = "generator_max_power_constraint"
    BATTERY_CHARGE_LIMIT = "battery_max_charge_constraint"
    BATTERY_DISCHARGE_LIMIT = "battery_max_discharge_constraint"
    BATTERY_SOC_DYNAMICS = "battery_soc_dynamics_constraint"
    BATTERY_SOC_BOUNDS = "battery_soc_bounds_constraint"
    BATTERY_SOC_START = "battery_soc_start_constraint"
    BATTERY_SOC_END = "battery_soc_end_constraint"
