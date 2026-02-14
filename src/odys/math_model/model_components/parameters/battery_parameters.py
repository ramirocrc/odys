"""Battery parameters for the mathematical optimization model."""

from collections.abc import Sequence
from typing import ClassVar

import xarray as xr

from odys.energy_system_models.assets.storage import Battery
from odys.math_model.model_components.sets import ModelDimension, ModelIndex


class BatteryIndex(ModelIndex, frozen=True):
    """Index for battery components in the optimization model."""

    dimension: ClassVar[ModelDimension] = ModelDimension.Batteries


class BatteryParameters:
    """Parameters for battery assets in the energy system model."""

    def __init__(self, batteries: Sequence[Battery]) -> None:
        """Initialize battery parameters.

        Args:
            batteries: Sequence of battery objects.
        """
        self._index = BatteryIndex(
            values=tuple(battery.name for battery in batteries),
        )
        data = {
            "capacity": [battery.capacity for battery in batteries],
            "max_power": [battery.max_power for battery in batteries],
            "efficiency_charging": [battery.efficiency_charging for battery in batteries],
            "efficiency_discharging": [battery.efficiency_discharging for battery in batteries],
            "soc_start": [battery.soc_start for battery in batteries],
            "soc_end": [battery.soc_end for battery in batteries],
            "soc_min": [battery.soc_min for battery in batteries],
            "soc_max": [battery.soc_max for battery in batteries],
        }
        dim = self._index.dimension
        self._dataset = xr.Dataset(
            {name: (dim, values) for name, values in data.items()},
            coords=self._index.coordinates,
        )

    @property
    def index(self) -> BatteryIndex:
        """Return the battery index."""
        return self._index

    @property
    def capacity(self) -> xr.DataArray:
        """Return battery capacity data."""
        return self._dataset["capacity"]

    @property
    def max_power(self) -> xr.DataArray:
        """Return battery maximum power data."""
        return self._dataset["max_power"]

    @property
    def efficiency_charging(self) -> xr.DataArray:
        """Return battery charging efficiency data."""
        return self._dataset["efficiency_charging"]

    @property
    def efficiency_discharging(self) -> xr.DataArray:
        """Return battery discharging efficiency data."""
        return self._dataset["efficiency_discharging"]

    @property
    def soc_start(self) -> xr.DataArray:
        """Return battery initial state of charge data."""
        return self._dataset["soc_start"]

    @property
    def soc_end(self) -> xr.DataArray:
        """Return battery final state of charge data."""
        return self._dataset["soc_end"]

    @property
    def soc_min(self) -> xr.DataArray:
        """Return battery minimum state of charge data."""
        return self._dataset["soc_min"]

    @property
    def soc_max(self) -> xr.DataArray:
        """Return battery maximum state of charge data."""
        return self._dataset["soc_max"]
