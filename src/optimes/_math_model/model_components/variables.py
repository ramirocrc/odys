"""Variable definitions for energy system optimization models.

This module defines variable names and types used in energy system
optimization models.
"""

from enum import Enum, unique

import pyomo.environ as pyo
from pydantic import BaseModel


@unique
class EnergyModelVariableName(Enum):
    """Enumeration of variable names used in the energy model."""

    GENERATOR_POWER = "var_generator_power"
    BATTERY_SOC = "var_battery_soc"
    BATTERY_CHARGE = "var_battery_charge"
    BATTERY_DISCHARGE = "var_battery_discharge"
    BATTERY_CHARGE_MODE = "var_battery_charge_mode"


class SystemVariable(BaseModel, arbitrary_types_allowed=True, extra="forbid"):
    """Container for Pyomo variable components in the energy system model.

    This class wraps Pyomo variables with their corresponding names for
    organized model construction and management.
    """

    name: EnergyModelVariableName
    component: pyo.Var
