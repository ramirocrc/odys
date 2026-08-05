"""Flexible load parameters for the mathematical optimization model."""

from collections.abc import Sequence

import xarray as xr

from odys.domain.entities.flexible_load import FlexibleLoad
from odys.domain.exceptions import OdysValidationError
from odys.optimization.model.dimensions import ModelDimension


class FlexibleLoadParameters:
    """Parameters for flexible load assets in the energy system model."""

    def __init__(self, flexible_loads: Sequence[FlexibleLoad]) -> None:
        """Initialize flexible load parameters.

        Args:
            flexible_loads: Non-empty sequence of flexible load objects.

        Raises:
            OdysValidationError: If flexible_loads is empty.
        """
        if not flexible_loads:
            msg = "FlexibleLoadParameters requires at least one flexible load."
            raise OdysValidationError(msg)
        names = [load.name for load in flexible_loads]
        dim = ModelDimension.FlexibleLoads
        data = {
            "max_increase": [load.max_increase for load in flexible_loads],
            "max_decrease": [load.max_decrease for load in flexible_loads],
            "value_of_consumption": [load.value_of_consumption for load in flexible_loads],
        }
        self._dataset = xr.Dataset(
            {name: (dim, values) for name, values in data.items()},
            coords={dim: names},
        )

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
