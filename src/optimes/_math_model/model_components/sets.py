from enum import StrEnum
from typing import ClassVar

from pydantic import BaseModel


class ModelDimension(StrEnum):
    Scenarios = "scenario"
    Time = "time"
    Generators = "generator"
    Batteries = "battery"


class ModelIndex(BaseModel):
    """Energy Model Set."""

    dimension: ClassVar[ModelDimension]
    values: list[str]

    @property
    def coordinates(self) -> dict[str, list[str]]:
        """Gets coordinates for xarray objects."""
        return {f"{self.dimension.value}": self.values}


class ScenarioIndex(ModelIndex):
    dimension: ClassVar[ModelDimension] = ModelDimension.Scenarios


class TimeIndex(ModelIndex):
    dimension: ClassVar[ModelDimension] = ModelDimension.Time


class GeneratorIndex(ModelIndex):
    dimension: ClassVar[ModelDimension] = ModelDimension.Generators


class BatteryIndex(ModelIndex):
    dimension: ClassVar[ModelDimension] = ModelDimension.Batteries
