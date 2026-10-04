"""Coordinate labels along one dimension of parameter arrays and model variables."""

from collections.abc import Sequence
from typing import Self

from pydantic import BaseModel, ConfigDict

from odys.domain.entities.base import EnergyEntity
from odys.parameters.dimensions import ModelDimension


class Coordinates(BaseModel):
    """Coordinate labels along a single dimension."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    dimension: ModelDimension
    labels: tuple[str, ...]

    @classmethod
    def of_entities(cls, dimension: ModelDimension, entities: Sequence[EnergyEntity]) -> Self:
        """Return coordinates labelled by the entities' names, in order.

        Args:
            dimension: The dimension the entities are indexed along.
            entities: The entities, such as all generators of the portfolio.

        Returns:
            The coordinates.

        """
        return cls(dimension=dimension, labels=tuple(entity.name for entity in entities))

    @property
    def dimension_coordinates_map(self) -> dict[str, list[str]]:
        """Return the xarray coordinate mapping for this dimension."""
        return {self.dimension.value: list(self.labels)}
