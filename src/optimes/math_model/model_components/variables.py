from enum import Enum, unique

import pyomo.environ as pyo
from pydantic import BaseModel


@unique
class EnergyModelVariableName(Enum):
    GENERATOR_POWER = "var_generator_power"
    BATTERY_CHARGE = "var_battery_charge"
    BATTERY_DISCHARGE = "var_battery_discharge"
    BATTERY_SOC = "var_battery_soc"
    BATTERY_CHARGE_MODE = "var_battery_charge_mode"


class SystemVariable(BaseModel, arbitrary_types_allowed=True, extra="forbid"):
    name: EnergyModelVariableName
    component: pyo.Var
