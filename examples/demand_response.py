"""Flexible load buying from a market.

This example shows how a flexible industrial consumer follows market prices.
Instead of consuming a fixed amount regardless of cost, the optimizer sets
the consumption at each step anywhere within the process's range, weighing
the value of consumption against the market price.

## Assets

- **market**: Buy-only electricity market with max 80 MW per timestep.
  Prices vary throughout the day from 30 to 90 $/MWh.
- **industrial_process**: Flexible load that can run anywhere from 40 to
  100 MW. Each MWh consumed has an economic value of 70 $/MWh.

## Problem

We simulate 24 hourly periods. At every step the optimizer chooses how much
the industrial process consumes, between 40 and 100 MW.

The decision compares the value of consumption (70 $/MWh) against the
market price at each step:
- When market price < 70 $/MWh: consuming more is profitable
- When market price > 70 $/MWh: consuming less saves money

## Expected Results

- Steps 3-16 (price 30-65 $/MWh): consumption rises to 80 MW, the market
  limit, although the process could take 100 MW.
- Steps 0-2 and 17-23 (price 72-90 $/MWh): consumption drops to 40 MW.

Each step is decided on its own: nothing links one hour to the next.

## Understanding the Output

The script prints:
- Consumption of the process over time
- Market purchases (matches the consumption at each timestep)
"""

import logging
from datetime import timedelta

from odys import (
    AllowedTradeDirection,
    AssetPortfolio,
    EnergyMarket,
    EnergySystem,
    FlexibleLoad,
    FlexibleLoadProfile,
    OptimalDispatchResults,
    PriceProfile,
    Scenario,
)

logger = logging.getLogger(__name__)


def run_demand_response() -> OptimalDispatchResults:
    """Run the industrial demand response example and return the optimization results."""
    market = EnergyMarket(
        name="market",
        max_trading_volume_per_step=80,
        allowed_trade_direction=AllowedTradeDirection.BUY_ONLY,
    )

    industrial_process = FlexibleLoad(name="industrial_process", value_of_consumption=70)

    portfolio = AssetPortfolio(assets=[industrial_process])

    scenario = Scenario(
        profiles=(
            FlexibleLoadProfile(load=industrial_process, lower_bound=24 * [40], upper_bound=24 * [100]),
            PriceProfile(
                market=market,
                values=[80, 75, 72, 65, 60, 55, 50, 45, 40, 35, 30, 35, 40, 45, 50, 55, 60, 72, 80, 90, 85, 80, 75, 72],
            ),
        ),
    )

    energy_system = EnergySystem(
        portfolio=portfolio,
        markets=market,
        timestep=timedelta(hours=1),
        number_of_steps=24,
        scenarios=scenario,
    )

    return energy_system.optimize()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logging.getLogger("linopy").setLevel(logging.WARNING)
    result = run_demand_response()

    logger.info("Consumption (MW)")
    logger.info(result.flexible_loads.consumption)

    logger.info("Market purchases (MW)")
    logger.info(result.markets.buy_volume)
