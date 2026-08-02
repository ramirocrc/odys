"""Market contributions to power balance and per-scenario profit."""

from __future__ import annotations

from typing import TYPE_CHECKING

from odys.optimization.model.sets import ModelDimension

if TYPE_CHECKING:
    import linopy

    from odys.optimization.model.milp_model import EnergyMILPModel
    from odys.optimization.parameters.parameters import EnergySystemParameters


def market_power_balance_terms(
    model: EnergyMILPModel,
    params: EnergySystemParameters,
) -> linopy.LinearExpression:
    """Net power injection from market trades, reduced to (scenario, time)."""
    del params
    return model.vars.market_buy_volume.sum(ModelDimension.Markets) - model.vars.market_sell_volume.sum(
        ModelDimension.Markets,
    )


def market_profit_terms(
    model: EnergyMILPModel,
    params: EnergySystemParameters,
) -> linopy.LinearExpression | None:
    """Market trade revenue/cost as profit, reduced to (scenario,).

    Returns None when scenario market prices are absent (matches prior kernel gate).
    """
    market_prices = params.scenarios.market_prices
    if market_prices is None:
        return None
    return (
        (model.vars.market_sell_volume - model.vars.market_buy_volume)  # pyrefly: ignore
        * market_prices
    ).sum([ModelDimension.Time, ModelDimension.Markets])
