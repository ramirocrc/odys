"""Parameter definitions for energy system optimization models.

This module defines parameter names and types used in energy system
optimization models.
"""

import xarray as xr
from pydantic import BaseModel

from optimes._math_model.model_components.sets import ModelSet


class GeneratorParameters(BaseModel, frozen=True, arbitrary_types_allowed=True, extra="forbid"):
    set: ModelSet
    nominal_power: xr.DataArray
    variable_cost: xr.DataArray
    min_up_time: xr.DataArray
    min_power: xr.DataArray
    startup_cost: xr.DataArray


class BatteryParameters(BaseModel, frozen=True, arbitrary_types_allowed=True, extra="forbid"):
    set: ModelSet
    capacity: xr.DataArray
    max_power: xr.DataArray
    efficiency_charging: xr.DataArray
    efficiency_discharging: xr.DataArray
    soc_start: xr.DataArray
    soc_end: xr.DataArray
    soc_min: xr.DataArray
    soc_max: xr.DataArray


class SystemParameters(BaseModel, frozen=True, arbitrary_types_allowed=True, extra="forbid"):
    time_set: ModelSet
    demand_profile: xr.DataArray


class EnergyModelParameters(BaseModel):
    generators: GeneratorParameters
    batteries: BatteryParameters
    system: SystemParameters
