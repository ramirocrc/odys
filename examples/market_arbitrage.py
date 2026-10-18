"""Market arbitrage with a gas plant and a two-way market.

This example adds a market to the dispatch problem. The site can buy power
instead of producing it, and sell what its gas plant produces beyond the
load. It shows how Odys compares a unit's operating cost against a market
price at every step.

## Assets

- **ccgt**: 100 MW gas turbine, variable cost of 50 $/MWh.
- **load**: Fixed electricity demand of 70 MW.
- **market**: Energy market that buys and sells, max 100 MW per timestep.
  Prices vary throughout the day from 30 to 90 $/MWh.

## Problem

We simulate 24 hourly periods with a constant 70 MW load. At each step, the
optimizer decides how much the ccgt produces and how much the site buys or
sells.

## Expected Results

- When the price is above 50 $/MWh: ccgt = 100 MW, serving the load and
  selling the other 30 MW.
- When the price is below 50 $/MWh: ccgt = 0, and the site buys the 70 MW.

## Understanding the Output

The script prints:
- Generator dispatch as a DataFrame showing ccgt output at each timestep
- Net market volume at each timestep (positive = sell, negative = buy)
"""

import logging
from datetime import timedelta

from odys import (
    AssetPortfolio,
    EnergyMarket,
    EnergySystem,
    FixedLoad,
    Generator,
    LoadProfile,
    OptimalDispatchResults,
    PriceProfile,
    Scenario,
)

logger = logging.getLogger(__name__)


def run_market_arbitrage() -> OptimalDispatchResults:
    """Run the market arbitrage example and return the optimization results."""
    ccgt = Generator(
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
    )

    portfolio = AssetPortfolio([ccgt, load])

    scenario = Scenario(
        profiles=(
            LoadProfile(load=load, values=24 * [70]),
            PriceProfile(
                market=market,
                values=[80, 75, 70, 65, 60, 55, 52, 45, 40, 35, 30, 35, 40, 45, 52, 55, 60, 70, 80, 90, 85, 80, 75, 70],
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
    result = run_market_arbitrage()
    logger.info(result.generators.to_dataframe())
    logger.info(result.markets.net_volume)
