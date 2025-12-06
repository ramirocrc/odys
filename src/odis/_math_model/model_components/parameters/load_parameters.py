"""Load parameters for the mathematical optimization model."""

from collections.abc import Sequence
from typing import ClassVar

from odis._math_model.model_components.sets import ModelDimension, ModelIndex
from odis.energy_system_models.assets.load import Load


class LoadIndex(ModelIndex, frozen=True):
    """Index for load components in the optimization model."""

    dimension: ClassVar[ModelDimension] = ModelDimension.Loads


class LoadParameters:
    """Parameters for load assets in the energy system model."""

    def __init__(self, loads: Sequence[Load]) -> None:
        """Initialize load parameters.

        Args:
            loads: Sequence of load objects.
        """
        self._loads = loads
        self._index = LoadIndex(
            values=tuple(gen.name for gen in self._loads),
        )

    @property
    def index(self) -> LoadIndex:
        """Return the load index."""
        return self._index
