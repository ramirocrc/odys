"""Energy market definitions for energy system models."""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class TradeDirection(StrEnum):
    """Direction of the market positions."""

    BUY_ONLY = "buy"
    SELL_ONLY = "sell"
    BUY_AND_SELL = "buy_and_sell"


class EnergyMarket(BaseModel):
    """Represents an energy market in the energy system."""

    model_config = ConfigDict(extra="forbid")

    name: str
    max_trading_volume_per_step: float = Field(gt=0)
    trade_direction: TradeDirection = TradeDirection.BUY_AND_SELL
    stage_fixed: bool = Field(
        default=False,
        description="If true, the associated variables are fixed across scenarios.",
    )
