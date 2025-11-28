"""Energy market definitions for energy system models."""

from enum import StrEnum

from pydantic import BaseModel, Field


class TradeDirection(StrEnum):
    """Direction of the market positions."""

    BUY = "buy"
    SELL = "sell"
    BOTH = "both"


class EnergyMarket(BaseModel, extra="forbid"):
    """Represents an energy market in the energy system."""

    name: str
    max_trading_volume_per_step: float = Field(gt=0)
    trade_direction: TradeDirection = TradeDirection.BOTH
    stage_fixed: bool = Field(
        default=False,
        description="If true, the associated varialbes are fixed accross scenarios.",
    )
