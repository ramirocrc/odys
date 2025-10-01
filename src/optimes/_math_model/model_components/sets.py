from enum import Enum

from pydantic import BaseModel


class EnergyModelDimension(Enum):
    Time = "time"
    Generators = "generators"
    Batteries = "batteries"
    Scenarios = "scenarios"


class ModelSet(BaseModel):
    """Energy Model Set."""

    dimension: EnergyModelDimension
    values: list[str]

    @property
    def coordinates(self) -> dict[str, list[str]]:
        """Gets coordinates for xarray objects."""
        return {f"{self.dimension.value}": self.values}
