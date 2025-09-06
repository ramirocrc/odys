"""Parameter definitions for energy system optimization models.

This module defines parameter names and types used in energy system
optimization models.
"""

import xarray as xr
from pydantic import BaseModel

from optimes._math_model.model_components.sets import ModelSet


class GeneratorParameters(BaseModel, frozen=True, arbitrary_types_allowed=True, extra="forbid"):
    set: ModelSet
    generators_nominal_power: xr.DataArray
    generators_variable_cost: xr.DataArray


class BatteryParameters(BaseModel, frozen=True, arbitrary_types_allowed=True, extra="forbid"):
    set: ModelSet
    batteries_capacity: xr.DataArray
    batteries_max_power: xr.DataArray
    batteries_efficiency_charging: xr.DataArray
    batteries_efficiency_discharging: xr.DataArray
    batteries_soc_start: xr.DataArray
    batteries_soc_end: xr.DataArray
    batteries_soc_min: xr.DataArray
    batteries_soc_max: xr.DataArray


class SystemParameters(BaseModel, frozen=True, arbitrary_types_allowed=True, extra="forbid"):
    time_set: ModelSet
    demand_profile: xr.DataArray


class EnergyModelParameters(BaseModel):
    generators: GeneratorParameters
    batteries: BatteryParameters
    system: SystemParameters
