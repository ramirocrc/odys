"""Flexible load with market price arbitrage.

This example shows how a flexible industrial consumer can shift electricity
consumption to take advantage of low market prices. Instead of consuming a
fixed amount regardless of cost, the optimizer adjusts demand up or down
based on the economic value of consumption versus the market price.

## Assets

- **market**: Buy-only electricity market with max 80 MW per timestep.
  Prices vary throughout the day from 30 to 90 $/MWh.
- **industrial_process**: Flexible load with a base consumption of 60 MW.
  Can increase up to 40 MW or decrease up to 20 MW from the base.
  Each MWh consumed has an economic value of 70 $/MWh.

## Problem

We simulate 24 hourly periods. The industrial process has a baseline
consumption of 60 MW, but the optimizer can adjust it within bounds.

The decision logic compares the marginal value of consumption (70 $/MWh)
against the marginal cost (market price):
- When market price < 70 $/MWh: consuming more is profitable
- When market price > 70 $/MWh: consuming less saves money
- When market price = 70 $/MWh: neutral, no adjustment

## Expected Results

The optimizer shifts consumption toward low-price hours:

- Hours 3-16 (price 30-65 $/MWh): Increase load to market limit (+20 MW)
  Total consumption = 80 MW. Market supplies all 80 MW.
- Hours 0-2, 17-23 (price 70-90 $/MWh): Decrease load (-20 MW)
  Total consumption = 40 MW. Market supplies only 40 MW.
- Hours 2, 23 (price 70 $/MWh): Neutral, consumption stays at 60 MW.

The net effect: the industrial process consumes 33% more energy during cheap
hours and 33% less during expensive hours, maximizing the economic value of
consumption. The market volume limit (80 MW) constrains how much the load
can increase, even though the process could flex up to 100 MW.

## Understanding the Output

The script prints:
- Load adjustment over time (positive = increase, negative = decrease)
- Actual consumption (base profile + adjustment)
- Market purchases (matches actual consumption at each timestep)

This example demonstrates demand response: the flexibility to shift when you
consume, not just how much you generate. The same principle applies to
data centers, aluminum smelters, water pumping, and other processes where
timing can be adjusted without affecting total output.
"""

from datetime import timedelta

from odys import AssetPortfolio, EnergyMarket, EnergySystem, FlexibleLoad, Scenario, TradeDirection
from odys.results.optimization_results import OptimalDisptachResults
from odys.utils.logging import get_logger, setup_rich_logging

setup_rich_logging()
logger = get_logger(__name__)


def run_flexible_load_market() -> OptimalDisptachResults:
    """Run the flexible load market example and return the optimization results."""
    market = EnergyMarket(
        name="market",
        max_trading_volume_per_step=80,
        trade_direction=TradeDirection.BUY_ONLY,
    )

    industrial_process = FlexibleLoad(
        name="industrial_process",
        max_increase=40,
        max_decrease=20,
        value_of_consumption=70,
    )

    portfolio = AssetPortfolio(assets=[industrial_process])

    scenario = Scenario(
        flexible_load_base_profiles={
            "industrial_process": 24 * [60],
        },
        market_prices={
            "market": [80, 75, 70, 65, 60, 55, 50, 45, 40, 35, 30, 35, 40, 45, 50, 55, 60, 70, 80, 90, 85, 80, 75, 70],
        },
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
    result = run_flexible_load_market()

    logger.info("Load adjustment (MW)")
    logger.info(result.flexible_loads.load_adjustment)

    logger.info("Actual consumption (MW)")
    logger.info(result.flexible_loads.actual_load)

    logger.info("Market purchases (MW)")
    logger.info(result.markets.buy_volume)
