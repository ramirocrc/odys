"""Market parameters for the mathematical optimization model."""

from collections.abc import Sequence
from typing import ClassVar

import xarray as xr

from optimes._math_model.model_components.sets import ModelDimension, ModelIndex
from optimes.energy_system_models.markets import EnergyMarket


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
        self._index = MarketIndex(
            values=tuple(market.name for market in self._markets),
        )

    @property
    def index(self) -> MarketIndex:
        """Return the market index."""
        return self._index

    @property
    def _market_max_volume(self) -> xr.DataArray:
        markets = [self._markets] if isinstance(self._markets, EnergyMarket) else self._markets
        market_max_volumes = [market.limit for market in markets]
        return xr.DataArray(
            data=market_max_volumes,
            coords=self.index.coordinates,
        )
