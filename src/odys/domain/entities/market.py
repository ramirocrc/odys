"""Energy market definitions for energy system models."""

from enum import StrEnum

from pydantic import Field

from odys.domain.entities.base import EnergyEntity


class TradeDirection(StrEnum):
    """Direction of the market positions."""

    BUY_ONLY = "buy"
    SELL_ONLY = "sell"
    BUY_AND_SELL = "buy_and_sell"


class EnergyMarket(EnergyEntity):
    """Represents an energy market in the energy system."""

    name: str
    max_trading_volume_per_step: float = Field(gt=0)
    trade_direction: TradeDirection = TradeDirection.BUY_AND_SELL
    stage_fixed: bool = Field(
        default=False,
        description="If true, the associated variables are fixed across scenarios.",
    )
