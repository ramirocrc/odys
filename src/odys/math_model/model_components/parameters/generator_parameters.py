"""Generator parameters for the mathematical optimization model."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

import xarray as xr

from odys.math_model.model_components.sets import ModelDimension, ModelIndex

if TYPE_CHECKING:
    from collections.abc import Sequence

    from odys.energy_system_models.assets.generator import Generator


class GeneratorIndex(ModelIndex):
    """Index for generator components in the optimization model."""

    dimension: ClassVar[ModelDimension] = ModelDimension.Generators


class GeneratorParameters:
    """Parameters for generator assets in the energy system model."""

    @classmethod
    def from_assets(cls, generators: Sequence[Generator]) -> GeneratorParameters | None:
        """Create generator parameters from a sequence of generators.

        Args:
            generators: Sequence of power generator objects.

        Returns:
            GeneratorParameters if generators is non-empty, None otherwise.

        """
        if not generators:
            return None
        return cls(generators=generators)

    def __init__(self, generators: Sequence[Generator]) -> None:
        """Initialize generator parameters.

        Args:
            generators: Sequence of power generator objects.
        """
        self._index = GeneratorIndex(
            values=tuple(gen.name for gen in generators),
        )
        data = {
            "nominal_power": [gen.nominal_power for gen in generators],
            "variable_cost": [gen.variable_cost for gen in generators],
            "min_up_time": [gen.min_up_time for gen in generators],
            "min_power": [gen.min_power for gen in generators],
            "startup_cost": [gen.startup_cost for gen in generators],
            "max_ramp_up": [gen.ramp_up for gen in generators],
            "max_ramp_down": [gen.ramp_down for gen in generators],
        }
        dim = self._index.dimension
        self._dataset = xr.Dataset(
            {name: (dim, values) for name, values in data.items()},
            coords=self._index.coordinates,
        )

    @property
    def index(self) -> GeneratorIndex:
        """Return the generator index."""
        return self._index

    @property
    def nominal_power(self) -> xr.DataArray:
        """Return generator nominal power data."""
        return self._dataset["nominal_power"]

    @property
    def variable_cost(self) -> xr.DataArray:
        """Return generator variable cost data."""
        return self._dataset["variable_cost"]

    @property
    def min_up_time(self) -> xr.DataArray:
        """Return generator minimum up time data."""
        return self._dataset["min_up_time"]

    @property
    def min_power(self) -> xr.DataArray:
        """Return generator minimum power data."""
        return self._dataset["min_power"]

    @property
    def startup_cost(self) -> xr.DataArray:
        """Return generator startup cost data."""
        return self._dataset["startup_cost"]

    @property
    def max_ramp_up(self) -> xr.DataArray:
        """Return generator maximum ramp up rate data."""
        return self._dataset["max_ramp_up"]

    @property
    def max_ramp_down(self) -> xr.DataArray:
        """Return generator maximum ramp down rate data."""
        return self._dataset["max_ramp_down"]
