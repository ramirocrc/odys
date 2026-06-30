"""Energy market definitions for energy system models."""

from enum import StrEnum

from pydantic import Field

from odys.domain.entities.base import EnergyEntity


class TradeDirection(StrEnum):
    """
Enumeration of supported market trading directions.

Trading directions specify whether an energy market permits buying,
selling, or both buying and selling during optimization.
"""

    BUY_ONLY = "buy"
    SELL_ONLY = "sell"
    BUY_AND_SELL = "buy_and_sell"


class EnergyMarket(EnergyEntity):
    """
Represents an energy market within the optimization model.

An energy market defines the trading environment for an energy system,
including the maximum trading volume, permitted trading direction, and
whether market-related decision variables remain fixed across scenarios.

Attributes:
    name: Unique name of the energy market.
    max_trading_volume_per_step: Maximum energy that can be traded in a
        single optimization step.
    trade_direction: Allowed trading direction for the market.
    stage_fixed: Indicates whether market variables are fixed across
        scenarios.
"""

    name: str
    max_trading_volume_per_step: float = Field(gt=0)
    trade_direction: TradeDirection = TradeDirection.BUY_AND_SELL
    stage_fixed: bool = Field(
        default=False,
        description="If true, the associated variables are fixed across scenarios.",
    )
