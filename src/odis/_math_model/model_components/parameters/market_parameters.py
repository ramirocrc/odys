"""Market parameters for the mathematical optimization model."""

from collections.abc import Sequence
from typing import ClassVar

import xarray as xr

from odis._math_model.model_components.sets import ModelDimension, ModelIndex
from odis.energy_system_models.markets import EnergyMarket


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
        self._markets = markets
        self._index = MarketIndex(values=tuple(market.name for market in self._markets))

    @property
    def index(self) -> MarketIndex:
        """Return the market index."""
        return self._index

    @property
    def max_volume(self) -> xr.DataArray:
        market_max_volumes = [market.max_trading_volume_per_step for market in self._markets]
        return xr.DataArray(
            data=market_max_volumes,
            coords=self.index.coordinates,
        )

    @property
    def stage_fixed(self) -> xr.DataArray:
        market_stage_fixed = [market.stage_fixed for market in self._markets]
        return xr.DataArray(
            data=market_stage_fixed,
            coords=self.index.coordinates,
        )

    @property
    def trade_direction(self) -> xr.DataArray:
        market_trade_direction = [market.trade_direction for market in self._markets]
        return xr.DataArray(
            data=market_trade_direction,
            coords=self.index.coordinates,
        )
