"""Battery parameters for the mathematical optimization model."""

from collections.abc import Sequence
from typing import ClassVar

import xarray as xr

from optimes._math_model.model_components.sets import ModelDimension, ModelIndex
from optimes.energy_system_models.assets.storage import Battery


class BatteryIndex(ModelIndex, frozen=True):
    """Index for battery components in the optimization model."""

    dimension: ClassVar[ModelDimension] = ModelDimension.Batteries


class BatteryParameters:
    """Parameters for battery assets in the energy system model."""

    def __init__(self, generators: Sequence[Battery]) -> None:
        """Initialize battery parameters.

        Args:
            generators: Sequence of battery objects.
        """
        self._batteries = generators
        self._index = BatteryIndex(
            values=tuple(battery.name for battery in self._batteries),
        )

    @property
    def index(self) -> BatteryIndex:
        """Return the battery index."""
        return self._index

    @property
    def capacity(self) -> xr.DataArray:
        """Return battery capacity data."""
        return xr.DataArray(
            data=[battery.capacity for battery in self._batteries],
            coords=self.index.coordinates,
        )

    @property
    def max_power(self) -> xr.DataArray:
        """Return battery maximum power data."""
        return xr.DataArray(
            data=[battery.max_power for battery in self._batteries],
            coords=self.index.coordinates,
        )

    @property
    def efficiency_charging(self) -> xr.DataArray:
        """Return battery charging efficiency data."""
        return xr.DataArray(
            data=[battery.efficiency_charging for battery in self._batteries],
            coords=self.index.coordinates,
        )

    @property
    def efficiency_discharging(self) -> xr.DataArray:
        """Return battery discharging efficiency data."""
        return xr.DataArray(
            data=[battery.efficiency_discharging for battery in self._batteries],
            coords=self.index.coordinates,
        )

    @property
    def soc_start(self) -> xr.DataArray:
        """Return battery initial state of charge data."""
        return xr.DataArray(
            data=[battery.soc_start for battery in self._batteries],
            coords=self.index.coordinates,
        )

    @property
    def soc_end(self) -> xr.DataArray:
        """Return battery final state of charge data."""
        return xr.DataArray(
            data=[battery.soc_end for battery in self._batteries],
            coords=self.index.coordinates,
        )

    @property
    def soc_min(self) -> xr.DataArray:
        """Return battery minimum state of charge data."""
        return xr.DataArray(
            data=[battery.soc_min for battery in self._batteries],
            coords=self.index.coordinates,
        )

    @property
    def soc_max(self) -> xr.DataArray:
        """Return battery maximum state of charge data."""
        batteries_soc_max = []
        for battery in self._batteries:
            battery_soc_max = battery.soc_max if battery.soc_max else battery.capacity
            batteries_soc_max.append(battery_soc_max)
        return xr.DataArray(
            data=batteries_soc_max,
            coords=self.index.coordinates,
        )
