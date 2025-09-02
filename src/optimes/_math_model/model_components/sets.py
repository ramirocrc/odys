from enum import Enum

from pydantic import BaseModel


class EnergyModelDimension(Enum):
    Time = "time"
    Generators = "generators"
    Batteries = "batteries"


class EnergyModelSet(BaseModel):
    """Energy Model Set."""

    dimension: EnergyModelDimension
    values: list[str]

    @property
    def coordinates(self) -> dict[str, list[str]]:
        """Get's coordinates for xarray objects."""
        return {f"{self.dimension.value}": self.values}


class EnergyModelSets(BaseModel, frozen=True):
    """Energy Model Sets."""

    time: EnergyModelSet
    generators: EnergyModelSet
    batteries: EnergyModelSet
