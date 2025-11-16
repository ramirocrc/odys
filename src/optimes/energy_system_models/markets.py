"""Energy market definitions for energy system models."""

from pydantic import BaseModel, Field


class EnergyMarket(BaseModel):
    """Represents an energy market in the energy system."""

    name: str
    limit: float = Field(gt=0)
