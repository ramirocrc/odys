from abc import ABC
from enum import StrEnum
from typing import ClassVar

from pydantic import BaseModel


class ModelDimension(StrEnum):
    Scenarios = "scenario"
    Time = "time"
    Generators = "generator"
    Batteries = "battery"
    Loads = "load"
    Markets = "market"


class ModelIndex(BaseModel, ABC, frozen=True):
    """Energy Model Set."""

    dimension: ClassVar[ModelDimension]
    values: tuple[str, ...]

    @property
    def coordinates(self) -> dict[str, list[str]]:
        """Gets coordinates for xarray objects."""
        return {f"{self.dimension}": list(self.values)}
