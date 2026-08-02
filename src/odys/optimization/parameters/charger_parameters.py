"""Charger parameters for the mathematical optimization model."""

from collections.abc import Sequence
from typing import ClassVar, Self

import xarray as xr

from odys.domain.entities.charger import Charger
from odys.optimization.model.sets import ModelDimension, ModelIndex
from odys.optimization.parameters.build_context import ParamBuildContext


class ChargerIndex(ModelIndex):
    """Index for charger components in the optimization model."""

    dimension: ClassVar[ModelDimension] = ModelDimension.Chargers


class ChargerParameters:
    """Parameters for charger assets in the energy system model."""

    def __init__(self, chargers: Sequence[Charger] | None = None) -> None:
        """Initialize charger parameters.

        Args:
            chargers: Sequence of charger objects.
        """
        self._chargers = list(chargers) if chargers else []
        self._index = ChargerIndex(
            values=tuple(charger.name for charger in self._chargers),
        )
        data = {
            "max_power": [charger.max_power for charger in self._chargers],
            "efficiency": [charger.efficiency for charger in self._chargers],
        }
        dim = self._index.dimension
        self._dataset = xr.Dataset(
            {name: (dim, values) for name, values in data.items()},
            coords=self._index.coordinates,
        )

    @classmethod
    def build(cls, ctx: ParamBuildContext) -> Self:
        """Build charger parameters from a parameter build context."""
        return cls(ctx.chargers)

    @property
    def is_empty(self) -> bool:
        """Return True if there are no chargers."""
        return len(self._chargers) == 0

    @property
    def index(self) -> ChargerIndex:
        """Return the charger index."""
        return self._index

    @property
    def max_power(self) -> xr.DataArray:
        """Return charger maximum power data."""
        return self._dataset["max_power"]

    @property
    def efficiency(self) -> xr.DataArray:
        """Return charger efficiency data."""
        return self._dataset["efficiency"]
