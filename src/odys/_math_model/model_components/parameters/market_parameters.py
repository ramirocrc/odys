"""Market parameters for the mathematical optimization model."""

from collections.abc import Sequence
from typing import ClassVar

import xarray as xr

from odys._math_model.model_components.sets import ModelDimension, ModelIndex
from odys.energy_system_models.markets import EnergyMarket


class MarketIndex(ModelIndex, frozen=True):
    """Index for market components in the optimization model."""

    dimension: ClassVar[ModelDimension] = ModelDimension.Markets


class MarketParameters:
    """Parameters for energy market components in the energy system model."""

    def __init__(self, markets: Sequence[EnergyMarket]) -> None:
        """Initialize market parameters.

        Args:
            markets: Sequence of energy market objects.
        """
        self._index = MarketIndex(values=tuple(market.name for market in markets))
        data = {
            "max_volume": [market.max_trading_volume_per_step for market in markets],
            "stage_fixed": [market.stage_fixed for market in markets],
            "trade_direction": [market.trade_direction for market in markets],
        }
        dim = self._index.dimension
        self._dataset = xr.Dataset(
            {name: (dim, values) for name, values in data.items()},
            coords=self._index.coordinates,
        )

    @property
    def index(self) -> MarketIndex:
        """Return the market index."""
        return self._index

    @property
    def max_volume(self) -> xr.DataArray:
        return self._dataset["max_volume"]

    @property
    def stage_fixed(self) -> xr.DataArray:
        return self._dataset["stage_fixed"]

    @property
    def trade_direction(self) -> xr.DataArray:
        return self._dataset["trade_direction"]
