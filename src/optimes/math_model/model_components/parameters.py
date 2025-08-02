from enum import Enum, unique

import pyomo.environ as pyo
from pydantic import BaseModel


@unique
class EnergyModelParameterName(Enum):
    """Enumeration of parameter names used in the energy model."""

    DEMAND = "param_demand"
    GENERATOR_NOMINAL_POWER = "param_generator_nominal_power"
    GENERATOR_VARIABLE_COST = "param_generator_variable_cost"
    BATTERY_MAX_POWER = "param_battery_max_power"
    BATTERY_EFFICIENCY_CHARGE = "param_battery_efficiency_charge"
    BATTERY_EFFICIENCY_DISCHARGE = "param_battery_efficiency_discharge"
    BATTERY_SOC_INITIAL = "param_battery_soc_initial"
    BATTERY_SOC_TERMINAL = "param_battery_soc_terminal"
    BATTERY_CAPACITY = "param_battery_capacity"
    SCENARIO_TIMESTEP = "param_scenario_timestep"


class SystemParameter(BaseModel, arbitrary_types_allowed=True, extra="forbid"):
    """Container for Pyomo parameter components in the energy system model.

    This class wraps Pyomo parameters with their corresponding names for
    organized model construction and management.
    """

    name: EnergyModelParameterName
    component: pyo.Param
