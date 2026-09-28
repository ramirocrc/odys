"""Charger parameters for the mathematical optimization model."""

from collections.abc import Sequence

import xarray as xr

from odys.domain.entities.charger import Charger
from odys.domain.exceptions import OdysValidationError
from odys.optimization.model.dimensions import ModelDimension


class ChargerParameters:
    """Parameters for charger assets in the energy system model."""

    def __init__(self, chargers: Sequence[Charger]) -> None:
        """Initialize charger parameters.

        Args:
            chargers: Non-empty sequence of charger objects.

        Raises:
            OdysValidationError: If chargers is empty.
        """
        if not chargers:
            msg = "ChargerParameters requires at least one charger."
            raise OdysValidationError(msg)
        names = [charger.name for charger in chargers]
        dim = ModelDimension.Chargers
        data = {
            "max_power": [charger.max_power for charger in chargers],
            "efficiency": [charger.efficiency for charger in chargers],
        }
        self._dataset = xr.Dataset(
            {name: (dim, values) for name, values in data.items()},
            coords={dim: names},
        )

    @property
    def max_power(self) -> xr.DataArray:
        """Return charger maximum power data."""
        return self._dataset["max_power"]

    @property
    def efficiency(self) -> xr.DataArray:
        """Return charger efficiency data."""
        return self._dataset["efficiency"]
