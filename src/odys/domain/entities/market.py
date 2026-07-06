"""Energy market definitions for energy system models."""

from enum import StrEnum

from pydantic import Field

from odys.domain.entities.base import EnergyEntity


class TradeDirection(StrEnum):
    """Allowed trading direction for an energy market.

    Determines whether a market permits buying energy, selling energy,
    or both. For ``BUY_AND_SELL`` markets, buying and selling are mutually
    exclusive within each timestep.
    """

    BUY_ONLY = "buy"
    SELL_ONLY = "sell"
    BUY_AND_SELL = "buy_and_sell"


class EnergyMarket(EnergyEntity):
    """An electricity market where the portfolio can buy or sell energy.

    An energy market enables the optimizer to procure or sell energy at
    scenario-specific prices defined in the scenario. The optimizer decides
    how much to buy or sell in each timestep, subject to volume limits and
    the permitted trading direction. Markets participate in the power balance
    constraint and contribute to the objective through trading revenue or cost.

    When ``stage_fixed`` is ``True``, trading decisions are locked before
    uncertainty is resolved — the same volumes apply across all stochastic
    scenarios. This models day-ahead or forward markets where commitments
    are made without knowing the realized future. Markets with
    ``stage_fixed`` ``False`` can react to each scenario independently.

    Attributes:
        name: Unique name of the energy market. Must match the corresponding
            key in the scenario's ``market_prices`` mapping.
        max_trading_volume_per_step: Maximum energy (in MW) that can be traded
            in a single optimization timestep.
        trade_direction: Allowed trading direction for the market.
        stage_fixed: If ``True``, trading volumes are fixed across all stochastic
            scenarios (non-anticipativity constraint).
    """

    name: str
    max_trading_volume_per_step: float = Field(gt=0)
    trade_direction: TradeDirection = TradeDirection.BUY_AND_SELL
    stage_fixed: bool = Field(
        default=False,
        description="If true, the associated variables are fixed across scenarios.",
    )
