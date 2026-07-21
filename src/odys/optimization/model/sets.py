"""Set and index definitions for the optimization model dimensions."""

from abc import ABC
from enum import StrEnum
from typing import ClassVar

from pydantic import BaseModel, ConfigDict


class ModelDimension(StrEnum):
    """Dimension names used as axes in the optimization model."""

    Scenarios = "scenario"
    Time = "time"
    Generators = "generator"
    Storages = "storage"
    FlexibleLoads = "flexible_load"
    Markets = "market"


class ModelIndex(BaseModel, ABC):
    """Energy Model Set."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
    )

    dimension: ClassVar[ModelDimension]
    values: tuple[str, ...]

    @property
    def coordinates(self) -> dict[str, list[str]]:
        """Gets coordinates for xarray objects."""
        return {f"{self.dimension}": list(self.values)}

    @property
    def is_empty(self) -> bool:
        """Return True if there are no values in this index."""
        return len(self.values) == 0
