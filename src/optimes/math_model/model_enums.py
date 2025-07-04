from enum import Enum


class EnergyModelSet(Enum):
    TIME = "time"
    GENERATORS = "generators"
    BATTERIES = "batteries"


class EnergyModelVariable(Enum):
    GENERATOR_POWER = "generator_power"
    BATTERY_CHARGE = "battery_charge"
    BATTERY_DISCHARGE = "battery_discharge"
    BATTERY_SOC = "battery_soc"
    BATTERY_CHARGE_MODE = "battery_charge_mode"


class EnergyModelConstraint(Enum):
    POWER_BALANCE = "power_balance"
    GENERATOR_LIMIT = "generator_limit"
    BATTERY_CHARGE_LIMIT = "battery_charge_limit"
    BATTERY_DISCHARGE_LIMIT = "battery_discharge_limit"
    BATTERY_SOC_DYNAMICS = "battery_soc_dynamics"
    BATTERY_SOC_BOUNDS = "battery_soc_bounds"
    BATTERY_SOC_TERMINAL = "battery_soc_terminal"


class EnergyModelObjective(Enum):
    MIN_OPERATIONAL_COST = "minimize_operational_cost"
