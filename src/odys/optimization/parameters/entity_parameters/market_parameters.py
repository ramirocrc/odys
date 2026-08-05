"""Market parameters for the mathematical optimization model."""

from collections.abc import Sequence

import xarray as xr

from odys.domain.entities.market import EnergyMarket
from odys.domain.exceptions import OdysValidationError
from odys.optimization.model.dimensions import ModelDimension


class MarketParameters:
    """Parameters for energy market components in the energy system model."""

    def __init__(self, markets: Sequence[EnergyMarket]) -> None:
        """Initialize market parameters.

        Args:
            markets: Non-empty sequence of energy market objects.

        Raises:
            OdysValidationError: If markets is empty.
        """
        if not markets:
            msg = "MarketParameters requires at least one market."
            raise OdysValidationError(msg)
        names = [market.name for market in markets]
        dim = ModelDimension.Markets
        data = {
            "max_volume": [market.max_trading_volume_per_step for market in markets],
            "stage_fixed": [market.stage_fixed for market in markets],
            "trade_direction": [market.trade_direction for market in markets],
        }
        self._dataset = xr.Dataset(
            {name: (dim, values) for name, values in data.items()},
            coords={dim: names},
        )

    @property
    def max_volume(self) -> xr.DataArray:
        """Return maximum trading volume per time step."""
        return self._dataset["max_volume"]

    @property
    def stage_fixed(self) -> xr.DataArray:
        """Return whether each market's variables are fixed across scenarios."""
        return self._dataset["stage_fixed"]

    @property
    def trade_direction(self) -> xr.DataArray:
        """Return the allowed trade direction (buy, sell, or both) per market."""
        return self._dataset["trade_direction"]
