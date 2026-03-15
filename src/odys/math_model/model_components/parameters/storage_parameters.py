"""Storage parameters for the mathematical optimization model."""

from collections.abc import Sequence
from typing import ClassVar

import xarray as xr

from odys.energy_system_models.assets.storage import Storage
from odys.math_model.model_components.sets import ModelDimension, ModelIndex


class StorageIndex(ModelIndex):
    """Index for storage components in the optimization model."""

    dimension: ClassVar[ModelDimension] = ModelDimension.Storages


class StorageParameters:
    """Parameters for storage assets in the energy system model."""

    def __init__(self, storages: Sequence[Storage]) -> None:
        """Initialize storage parameters.

        Args:
            storages: Sequence of storage objects.
        """
        self._index = StorageIndex(
            values=tuple(storage.name for storage in storages),
        )
        data = {
            "capacity": [storage.capacity for storage in storages],
            "max_power": [storage.max_power for storage in storages],
            "efficiency_charging": [storage.efficiency_charging for storage in storages],
            "efficiency_discharging": [storage.efficiency_discharging for storage in storages],
            "soc_start": [storage.soc_start for storage in storages],
            "soc_end": [storage.soc_end for storage in storages],
            "soc_min": [storage.soc_min for storage in storages],
            "soc_max": [storage.soc_max for storage in storages],
        }
        dim = self._index.dimension
        self._dataset = xr.Dataset(
            {name: (dim, values) for name, values in data.items()},
            coords=self._index.coordinates,
        )

    @property
    def index(self) -> StorageIndex:
        """Return the storage index."""
        return self._index

    @property
    def capacity(self) -> xr.DataArray:
        """Return storage capacity data."""
        return self._dataset["capacity"]

    @property
    def max_power(self) -> xr.DataArray:
        """Return storage maximum power data."""
        return self._dataset["max_power"]

    @property
    def efficiency_charging(self) -> xr.DataArray:
        """Return storage charging efficiency data."""
        return self._dataset["efficiency_charging"]

    @property
    def efficiency_discharging(self) -> xr.DataArray:
        """Return storage discharging efficiency data."""
        return self._dataset["efficiency_discharging"]

    @property
    def soc_start(self) -> xr.DataArray:
        """Return storage initial state of charge data."""
        return self._dataset["soc_start"]

    @property
    def soc_end(self) -> xr.DataArray:
        """Return storage final state of charge data."""
        return self._dataset["soc_end"]

    @property
    def soc_min(self) -> xr.DataArray:
        """Return storage minimum state of charge data."""
        return self._dataset["soc_min"]

    @property
    def soc_max(self) -> xr.DataArray:
        """Return storage maximum state of charge data."""
        return self._dataset["soc_max"]
