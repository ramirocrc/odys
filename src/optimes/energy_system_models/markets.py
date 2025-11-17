"""Energy market definitions for energy system models."""

from pydantic import BaseModel, Field


class EnergyMarket(BaseModel):
    """Represents an energy market in the energy system."""

    name: str
    max_trading_volume: float = Field(gt=0)
