from abc import ABC
from enum import Enum
from typing import ClassVar

from pydantic import BaseModel


class EnergyModelDimension(str, Enum):
    Time = "time"
    Generators = "generators"
    Batteries = "batteries"


class EnergyModelSet(ABC, BaseModel):
    """Energy Model Set."""

    dimension: ClassVar[EnergyModelDimension]
    values: list[str]

    @property
    def coordinates(self) -> dict[str, list[str]]:
        """Get's coordinates for xarray objects."""
        return {f"{self.dimension.value}": self.values}


class TimeSet(EnergyModelSet):
    dimension: ClassVar = EnergyModelDimension.Time


class GeneratorsSet(EnergyModelSet):
    dimension: ClassVar = EnergyModelDimension.Generators


class BatteriesSet(EnergyModelSet):
    dimension: ClassVar = EnergyModelDimension.Batteries


class EnergyModelSets(BaseModel, frozen=True):
    """Energy Model Sets."""

    time: TimeSet
    generators: GeneratorsSet
    batteries: BatteriesSet
