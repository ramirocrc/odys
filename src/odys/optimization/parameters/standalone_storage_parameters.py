"""Standalone storage parameters for the mathematical optimization model."""

from collections.abc import Sequence
from typing import ClassVar

import xarray as xr

from odys.domain.entities.standalone_storage import StandaloneStorage
from odys.optimization.model.sets import ModelDimension, ModelIndex


class StandaloneStorageIndex(ModelIndex):
    """Index for standalone storage components in the optimization model."""

    dimension: ClassVar[ModelDimension] = ModelDimension.StandaloneStorages


class StandaloneStorageParameters:
    """Parameters for standalone storage assets in the energy system model."""

    def __init__(self, storages: Sequence[StandaloneStorage] | None = None) -> None:
        """Initialize standalone storage parameters.

        Args:
            storages: Sequence of standalone storage objects.
        """
        self._storages = list(storages) if storages else []
        self._index = StandaloneStorageIndex(
            values=tuple(storage.name for storage in self._storages),
        )
        data = {
            "capacity": [storage.capacity for storage in self._storages],
            "max_charge_power": [storage.max_charge_power for storage in self._storages],
            "max_discharge_power": [storage.max_discharge_power for storage in self._storages],
            "efficiency_charging": [storage.efficiency_charging for storage in self._storages],
            "efficiency_discharging": [storage.efficiency_discharging for storage in self._storages],
            "self_discharge_rate": [storage.self_discharge_rate for storage in self._storages],
            "soc_start": [storage.soc_start for storage in self._storages],
            "soc_end": [storage.soc_end for storage in self._storages],
            "soc_min": [storage.soc_min for storage in self._storages],
            "soc_max": [storage.soc_max for storage in self._storages],
            "degradation_cost": [storage.degradation_cost for storage in self._storages],
        }
        dim = self._index.dimension
        self._dataset = xr.Dataset(
            {name: (dim, values) for name, values in data.items()},
            coords=self._index.coordinates,
        )

    @property
    def is_empty(self) -> bool:
        """Return True if there are no standalone storages."""
        return len(self._storages) == 0

    @property
    def index(self) -> StandaloneStorageIndex:
        """Return the standalone storage index."""
        return self._index

    @property
    def capacity(self) -> xr.DataArray:
        """Return standalone storage capacity data."""
        return self._dataset["capacity"]

    @property
    def max_charge_power(self) -> xr.DataArray:
        """Return standalone storage maximum charging power data."""
        return self._dataset["max_charge_power"]

    @property
    def max_discharge_power(self) -> xr.DataArray:
        """Return standalone storage maximum discharging power data."""
        return self._dataset["max_discharge_power"]

    @property
    def efficiency_charging(self) -> xr.DataArray:
        """Return standalone storage charging efficiency data."""
        return self._dataset["efficiency_charging"]

    @property
    def efficiency_discharging(self) -> xr.DataArray:
        """Return standalone storage discharging efficiency data."""
        return self._dataset["efficiency_discharging"]

    @property
    def self_discharge_rate(self) -> xr.DataArray:
        """Return standalone storage self discharge rate data."""
        return self._dataset["self_discharge_rate"]

    @property
    def soc_start(self) -> xr.DataArray:
        """Return standalone storage initial state of charge data."""
        return self._dataset["soc_start"]

    @property
    def soc_end(self) -> xr.DataArray:
        """Return standalone storage final state of charge data."""
        return self._dataset["soc_end"]

    @property
    def soc_min(self) -> xr.DataArray:
        """Return standalone storage minimum state of charge data."""
        return self._dataset["soc_min"]

    @property
    def soc_max(self) -> xr.DataArray:
        """Return standalone storage maximum state of charge data."""
        return self._dataset["soc_max"]

    @property
    def degradation_cost(self) -> xr.DataArray:
        """Return standalone storage degradation cost data."""
        return self._dataset["degradation_cost"]
