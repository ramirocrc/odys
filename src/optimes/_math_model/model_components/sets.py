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


class ScenarioIndex(ModelIndex, frozen=True):
    dimension: ClassVar[ModelDimension] = ModelDimension.Scenarios


class TimeIndex(ModelIndex, frozen=True):
    dimension: ClassVar[ModelDimension] = ModelDimension.Time


class GeneratorIndex(ModelIndex, frozen=True):
    dimension: ClassVar[ModelDimension] = ModelDimension.Generators


class BatteryIndex(ModelIndex, frozen=True):
    dimension: ClassVar[ModelDimension] = ModelDimension.Batteries


class LoadIndex(ModelIndex, frozen=True):
    dimension: ClassVar[ModelDimension] = ModelDimension.Loads


class MarketIndex(ModelIndex, frozen=True):
    dimension: ClassVar[ModelDimension] = ModelDimension.Markets
