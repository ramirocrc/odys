"""CVaR optimization example with non-zero shortfalls.

Three scenarios with different sidc prices. Sidc has a higher expected revenue
than sdac (avg 216 vs 200), so with a small CVaR weight the optimizer sells
everything in sidc. The low-price scenario (sidc=50) then falls well below the
VaR threshold, producing a non-zero shortfall.

Try increasing the CVaRTerm weight to see how the optimizer gradually shifts
capacity to sdac, reducing the shortfall at the cost of expected revenue.
"""

from datetime import timedelta

from odys import (
    AssetPortfolio,
    CVaRTerm,
    EnergyMarket,
    EnergySystem,
    Generator,
    Objective,
    StochasticScenario,
    TradeDirection,
)
from odys.utils.logging import get_logger, setup_rich_logging

setup_rich_logging()
logger = get_logger(__name__)

if __name__ == "__main__":
    ccgt = Generator(name="ccgt", nominal_power=100.0, variable_cost=20.0)

    portfolio = AssetPortfolio()
    portfolio.add_assets(ccgt)

    sdac = EnergyMarket(
        name="sdac",
        max_trading_volume_per_step=150,
        stage_fixed=True,
        trade_direction=TradeDirection.SELL_ONLY,
    )
    sidc = EnergyMarket(
        name="sidc",
        max_trading_volume_per_step=100,
        trade_direction=TradeDirection.SELL_ONLY,
    )

    energy_system = EnergySystem(
        portfolio=portfolio,
        markets=[sdac, sidc],
        scenarios=[
            StochasticScenario(
                name="high",
                probability=1 / 3,
                available_capacity_profiles={"ccgt": 4 * [100]},
                market_prices={"sdac": 4 * [200], "sidc": 4 * [500]},
            ),
            StochasticScenario(
                name="mid",
                probability=1 / 3,
                available_capacity_profiles={"ccgt": 4 * [100]},
                market_prices={"sdac": 4 * [200], "sidc": 4 * [200]},
            ),
            StochasticScenario(
                name="low",
                probability=1 / 3,
                available_capacity_profiles={"ccgt": 4 * [100]},
                market_prices={"sdac": 4 * [200], "sidc": 4 * [15]},
            ),
        ],
        timestep=timedelta(minutes=30),
        number_of_steps=4,
        power_unit="MW",
        objective=Objective(
            cvar=CVaRTerm(weight=0.0001, confidence_level=0.6),
        ),
    )

    result = energy_system.optimize()
    logger.info(result.termination_condition)
    logger.info("sell volume")
    logger.info(result.markets.sell_volume)
    logger.info("VaR:  %s", result.cvar.value_at_risk)
    logger.info("CVaR: %s", result.cvar.cvar)
    logger.info("shortfall per scenario:\n%s", result.cvar.shortfall_per_scenario)
