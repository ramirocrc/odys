"""Load parameters for the mathematical optimization model."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from odys.math_model.model_components.sets import ModelDimension, ModelIndex

if TYPE_CHECKING:
    from collections.abc import Sequence

    from odys.energy_system_models.assets.load import Load


class LoadIndex(ModelIndex):
    """Index for load components in the optimization model."""

    dimension: ClassVar[ModelDimension] = ModelDimension.Loads


class LoadParameters:
    """Parameters for load assets in the energy system model."""

    @classmethod
    def from_assets(cls, loads: Sequence[Load]) -> LoadParameters | None:
        """Create load parameters from a sequence of loads.

        Args:
            loads: Sequence of load objects.

        Returns:
            LoadParameters if loads is non-empty, None otherwise.

        """
        if not loads:
            return None
        return cls(loads=loads)

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
