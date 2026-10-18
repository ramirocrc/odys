"""Risk-aware market allocation with CVaR.

This example shows how Odys trades off expected profit against downside risk.
Selling a gas plant's output on the riskier market pays more on average, but
once bad outcomes are weighed in, a commitment to the steadier market wins.

## Assets

- **ccgt**: 100 MW gas turbine, variable cost of 20 $/MWh.

## Markets

- **day_ahead**: Sell-only market (SDAC), bid before the scenario is known
  (stage_fixed=True). Prices by scenario: 190, 200, 210 $/MWh.
- **intraday**: Sell-only market (SIDC), traded once the scenario is known.
  Prices by scenario: 280 (high), 200 (mid), 140 (low) $/MWh.

## Problem

One hourly step with three equally likely scenarios. The optimizer splits the
ccgt's 100 MW between the two markets, in two runs:
1. **Expected profit only.**
2. **Expected profit plus CVaR** (weight 1, confidence level 0.6).

## Expected Results

| Allocation (day-ahead / intraday) | high   | mid    | low    | Expected | CVaR   |
|-----------------------------------|--------|--------|--------|----------|--------|
| 100 / 0                           | 17,000 | 18,000 | 19,000 | 18,000   | 17,167 |
| 0 / 100                           | 26,000 | 18,000 | 12,000 | 18,667   | 13,000 |
| 87.5 / 12.5                       | 18,125 | 18,000 | 18,125 | 18,083   | 18,021 |

1. Expected profit only: 100 MW intraday, objective 18,667.
2. With CVaR: 87.5 MW day-ahead and 12.5 MW intraday, objective 36,104.
"""

import logging
from datetime import timedelta

from odys import (
    AllowedTradeDirection,
    AssetPortfolio,
    CVaRTerm,
    EnergyMarket,
    EnergySystem,
    Generator,
    Objective,
    OptimalDispatchResults,
    PriceProfile,
    ProfitTerm,
    Scenario,
)

logger = logging.getLogger(__name__)

CCGT_VARIABLE_COST = 20.0
SCENARIO_PRICES: dict[str, dict[str, float]] = {
    "high": {"day_ahead": 190, "intraday": 280},
    "mid": {"day_ahead": 200, "intraday": 200},
    "low": {"day_ahead": 210, "intraday": 140},
}


def run_cvar_market_risk() -> tuple[OptimalDispatchResults, OptimalDispatchResults]:
    """Run the CVaR market risk example and return both optimization results."""
    ccgt = Generator(name="ccgt", nominal_power=100.0, variable_cost=CCGT_VARIABLE_COST)

    portfolio = AssetPortfolio([ccgt])

    day_ahead = EnergyMarket(
        name="day_ahead",
        max_trading_volume_per_step=150,
        stage_fixed=True,
        allowed_trade_direction=AllowedTradeDirection.SELL_ONLY,
    )
    intraday = EnergyMarket(
        name="intraday",
        max_trading_volume_per_step=100,
        allowed_trade_direction=AllowedTradeDirection.SELL_ONLY,
    )

    scenarios = [
        Scenario(
            name=name,
            probability=1 / len(SCENARIO_PRICES),
            profiles=(
                PriceProfile(market=day_ahead, values=[prices["day_ahead"]]),
                PriceProfile(market=intraday, values=[prices["intraday"]]),
            ),
        )
        for name, prices in SCENARIO_PRICES.items()
    ]

    energy_system_max_expected_profit = EnergySystem(
        portfolio=portfolio,
        markets=[day_ahead, intraday],
        scenarios=scenarios,
        number_of_steps=1,
        timestep=timedelta(hours=1),
        objective=Objective(terms=(ProfitTerm(weight=1),)),
    )
    result_max_expected_profit = energy_system_max_expected_profit.optimize()

    energy_system_penalized_cvar = EnergySystem(
        portfolio=portfolio,
        markets=[day_ahead, intraday],
        scenarios=scenarios,
        number_of_steps=1,
        timestep=timedelta(hours=1),
        objective=Objective(
            terms=(
                ProfitTerm(weight=1),
                CVaRTerm(weight=1, confidence_level=0.6),
            ),
        ),
    )
    result_penalized_cvar = energy_system_penalized_cvar.optimize()

    return result_max_expected_profit, result_penalized_cvar


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logging.getLogger("linopy").setLevel(logging.WARNING)
    result_max_expected_profit, result_penalized_cvar = run_cvar_market_risk()
    logger.info("optimal solution for max expected profit")
    logger.info(result_max_expected_profit.markets.sell_volume)

    logger.info("optimal solution penalizing cvar")
    logger.info(result_penalized_cvar.markets.sell_volume)
