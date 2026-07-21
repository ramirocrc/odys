"""Flexible load parameters for the mathematical optimization model."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

import xarray as xr

from odys.optimization.model.sets import ModelDimension, ModelIndex

if TYPE_CHECKING:
    from collections.abc import Sequence

    from odys.domain.entities.flexible_load import FlexibleLoad


class FlexibleLoadIndex(ModelIndex):
    """Index for flexible load components in the optimization model."""

    dimension: ClassVar[ModelDimension] = ModelDimension.FlexibleLoads


class FlexibleLoadParameters:
    """Parameters for flexible load assets in the energy system model."""

    def __init__(self, flexible_loads: Sequence[FlexibleLoad] | None = None) -> None:
        """Initialize flexible load parameters.

        Args:
            flexible_loads: Sequence of flexible load objects.
        """
        self._flexible_loads = list(flexible_loads) if flexible_loads else []
        self._index = FlexibleLoadIndex(
            values=tuple(load.name for load in self._flexible_loads),
        )
        data = {
            "max_increase": [load.max_increase for load in self._flexible_loads],
            "max_decrease": [load.max_decrease for load in self._flexible_loads],
            "value_of_consumption": [load.value_of_consumption for load in self._flexible_loads],
        }
        dim = self._index.dimension
        self._dataset = xr.Dataset(
            {name: (dim, values) for name, values in data.items()},
            coords=self._index.coordinates,
        )

    @property
    def is_empty(self) -> bool:
        """Return True if there are no flexible loads."""
        return len(self._flexible_loads) == 0

    @property
    def index(self) -> FlexibleLoadIndex:
        """Return the flexible load index."""
        return self._index

    @property
    def max_increase(self) -> xr.DataArray:
        """Return maximum increase data."""
        return self._dataset["max_increase"]

    @property
    def max_decrease(self) -> xr.DataArray:
        """Return maximum decrease data."""
        return self._dataset["max_decrease"]

    @property
    def value_of_consumption(self) -> xr.DataArray:
        """Return value of consumption data."""
        return self._dataset["value_of_consumption"]
