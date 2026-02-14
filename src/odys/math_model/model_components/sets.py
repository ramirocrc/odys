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
    Batteries = "battery"
    Loads = "load"
    Markets = "market"


class ModelIndex(BaseModel, ABC):  # pyright: ignore[reportUnsafeMultipleInheritance]
    """Energy Model Set."""

    dimension: ClassVar[ModelDimension]
    model_config = ConfigDict(frozen=True)
    values: tuple[str, ...]

    @property
    def coordinates(self) -> dict[str, list[str]]:
        """Gets coordinates for xarray objects."""
        return {f"{self.dimension}": list(self.values)}
