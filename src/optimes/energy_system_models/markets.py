"""Energy market definitions for energy system models."""

from pydantic import BaseModel


class EnergyMarket(BaseModel):
    """Represents an energy market in the energy system."""

    name: str
