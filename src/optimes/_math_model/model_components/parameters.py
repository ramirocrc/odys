"""Parameter definitions for energy system optimization models.

This module defines parameter names and types used in energy system
optimization models.
"""

import xarray as xr
from pydantic import BaseModel


class EnergyModelParameters(BaseModel, frozen=True, arbitrary_types_allowed=True, extra="forbid"):
    generators_nomianl_power: xr.DataArray
    generators_variable_cost: xr.DataArray
    batteries_capacity: xr.DataArray
    batteries_max_power: xr.DataArray
    batteries_efficiency_charging: xr.DataArray
    batteries_efficiency_discharging: xr.DataArray
    batteries_soc_start: xr.DataArray
    batteries_soc_end: xr.DataArray
    demand_profile: xr.DataArray
