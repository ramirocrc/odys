from pydantic import BaseModel


class EnergyModelSet(BaseModel, frozen=True):
    """Energy Model Set."""

    dimension: str
    values: list[str]

    @property
    def coordinates(self) -> dict[str, list[str]]:
        """Get's coordinates for xarray objects."""
        return {f"{self.dimension}": self.values}


class EnergyModelSets(BaseModel, frozen=True):
    """Energy Model Sets."""

    time: EnergyModelSet
    generators: EnergyModelSet
    batteries: EnergyModelSet
