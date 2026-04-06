"""Market parameters for the mathematical optimization model."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

import xarray as xr

from odys.optimization.model.sets import ModelDimension, ModelIndex

if TYPE_CHECKING:
    from collections.abc import Sequence

    from odys.domain.entities.market import EnergyMarket


class MarketIndex(ModelIndex):
    """Index for market components in the optimization model."""

    dimension: ClassVar[ModelDimension] = ModelDimension.Markets


class MarketParameters:
    """Parameters for energy market components in the energy system model."""

    def __init__(self, markets: Sequence[EnergyMarket] | None = None) -> None:
        """Initialize market parameters.

        Args:
            markets: Sequence of energy market objects.
        """
        self._markets = list(markets) if markets else []
        self._index = MarketIndex(values=tuple(market.name for market in self._markets))
        data = {
            "max_volume": [market.max_trading_volume_per_step for market in self._markets],
            "stage_fixed": [market.stage_fixed for market in self._markets],
            "trade_direction": [market.trade_direction for market in self._markets],
        }
        dim = self._index.dimension
        self._dataset = xr.Dataset(
            {name: (dim, values) for name, values in data.items()},
            coords=self._index.coordinates,
        )

    @property
    def is_empty(self) -> bool:
        """Return True if there are no markets."""
        return len(self._markets) == 0

    @property
    def index(self) -> MarketIndex:
        """Return the market index."""
        return self._index

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
