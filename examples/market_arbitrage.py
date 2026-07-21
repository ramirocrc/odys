"""Market arbitrage with a buy-only electricity market.

This example adds a market to the dispatch problem so the optimizer can choose
between self-generation and buying energy. It is a good way to see how Odys
compares operating cost against market price.

## Assets

- **ccgt**: 100 MW gas turbine, variable cost of 50 $/MWh, fully available
  24/7.
- **load**: Fixed electricity demand of 70 MW.
- **market**: Energy market with buy-only capability, max 100 MW per timestep.

## Problem

We simulate 24 hourly periods with a constant 70 MW load.
Market prices change over time, so the optimizer has to decide step by step
whether it is cheaper to generate locally or buy from the market.

## Expected Results

The optimizer buys from the market whenever the market price is below the
ccgt's marginal cost of 50 $/MWh. When the market is more expensive, the gas
plant takes over.

Market prices vary throughout the day, with some hours below 50 $/MWh and
others above, creating arbitrage opportunities.

For example:
- When market price = 80 $/MWh: ccgt = 70 MW  # price > 50, generate
- When market price = 40 $/MWh: market = 70 MW  # price < 50, buy
- When market price = 30 $/MWh: market = 70 MW  # price < 50, buy

## Understanding the Output

The script prints:
- Generator dispatch as a DataFrame showing ccgt output at each timestep
- (Market purchases can be viewed via result.markets)

Because the market is buy-only, the optimizer never sells excess power. That
keeps the example focused on a single question: when should you generate, and
when should you simply buy?
"""

from datetime import timedelta

from odys import AssetPortfolio, EnergyMarket, EnergySystem, FixedLoad, Generator, Scenario, TradeDirection
from odys.results.optimization_results import OptimalDisptachResults
from odys.utils.logging import get_logger, setup_rich_logging

setup_rich_logging()
logger = get_logger(__name__)


def run_market_arbitrage() -> OptimalDisptachResults:
    """Run the market arbitrage example and return the optimization results."""
    generator_1 = Generator(
        name="ccgt",
        nominal_power=100,
        variable_cost=50,
    )
    load = FixedLoad(
        name="load",
    )

    market = EnergyMarket(
        name="market",
        max_trading_volume_per_step=100,
        trade_direction=TradeDirection.BUY_ONLY,
    )

    portfolio = AssetPortfolio(assets=[generator_1, load])

    scenario = Scenario(
        available_capacity_profiles={
            "ccgt": 24 * [100],
        },
        fixed_load_profiles={
            "load": 24 * [70],
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
    result = run_market_arbitrage()
    logger.info(result.generators.to_dataframe())
