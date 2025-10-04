from enum import StrEnum

from pydantic import BaseModel


class EnergyModelDimension(StrEnum):
    Time = "time"
    Generators = "generator"
    Batteries = "battery"
    Scenarios = "scenario"


class ModelSet(BaseModel):
    """Energy Model Set."""

    dimension: EnergyModelDimension
    values: list[str]

    @property
    def coordinates(self) -> dict[str, list[str]]:
        """Gets coordinates for xarray objects."""
        return {f"{self.dimension.value}": self.values}
