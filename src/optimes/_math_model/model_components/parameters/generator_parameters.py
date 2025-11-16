"""Generator parameters for the mathematical optimization model."""

from collections.abc import Sequence
from typing import ClassVar

import xarray as xr

from optimes._math_model.model_components.sets import ModelDimension, ModelIndex
from optimes.energy_system_models.assets.generator import PowerGenerator


class GeneratorIndex(ModelIndex, frozen=True):
    """Index for generator components in the optimization model."""

    dimension: ClassVar[ModelDimension] = ModelDimension.Generators


class GeneratorParameters:
    """Parameters for generator assets in the energy system model."""

    def __init__(self, generators: Sequence[PowerGenerator]) -> None:
        """Initialize generator parameters.

        Args:
            generators: Sequence of power generator objects.
        """
        self._generators = generators
        self._index = GeneratorIndex(
            values=tuple(gen.name for gen in self._generators),
        )

    @property
    def index(self) -> GeneratorIndex:
        """Return the generator index."""
        return self._index

    @property
    def nominal_power(self) -> xr.DataArray:
        """Return generator nominal power data."""
        return xr.DataArray(
            data=[gen.nominal_power for gen in self._generators],
            coords=self._index.coordinates,
        )

    @property
    def variable_cost(self) -> xr.DataArray:
        """Return generator variable cost data."""
        return xr.DataArray(
            data=[gen.variable_cost for gen in self._generators],
            coords=self._index.coordinates,
        )

    @property
    def min_up_time(self) -> xr.DataArray:
        """Return generator minimum up time data."""
        return xr.DataArray(
            data=[gen.min_up_time for gen in self._generators],
            coords=self._index.coordinates,
        )

    @property
    def min_power(self) -> xr.DataArray:
        """Return generator minimum power data."""
        return xr.DataArray(
            data=[gen.min_power for gen in self._generators],
            coords=self._index.coordinates,
        )

    @property
    def startup_cost(self) -> xr.DataArray:
        """Return generator startup cost data."""
        return xr.DataArray(
            data=[gen.startup_cost for gen in self._generators],
            coords=self._index.coordinates,
        )

    @property
    def max_ramp_up(self) -> xr.DataArray:
        """Return generator maximum ramp up rate data."""
        return xr.DataArray(
            data=[gen.ramp_up for gen in self._generators],
            coords=self._index.coordinates,
        )

    @property
    def max_ramp_down(self) -> xr.DataArray:
        """Return generator maximum ramp down rate data."""
        return xr.DataArray(
            data=[gen.ramp_down for gen in self._generators],
            coords=self._index.coordinates,
        )
