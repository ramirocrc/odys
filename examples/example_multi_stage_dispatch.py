"""Energy system optimization example.

This module demonstrates the usage of the odys library for energy system optimization.
It creates a simple energy system with generators and batteries, then optimizes
the system operation to meet demand at minimum cost.
"""

from datetime import timedelta

from odys import (
    AssetPortfolio,
    EnergyMarket,
    EnergySystem,
    Generator,
    StochasticScenario,
    TradeDirection,
)
from odys.optimization.cvar_config import CVaRConfig
from odys.utils.logging import get_logger, setup_rich_logging

setup_rich_logging()
logger = get_logger(__name__)

if __name__ == "__main__":
    ccgt_unit = Generator(
        name="ccgt",
        nominal_power=100.0,
        variable_cost=20.0,
    )

    portfolio = AssetPortfolio()
    portfolio.add_assets(ccgt_unit)

    sdac_market = EnergyMarket(
        name="sdac",
        max_trading_volume_per_step=150,
        stage_fixed=True,
        trade_direction=TradeDirection.SELL_ONLY,
    )
    sidc_market = EnergyMarket(
        name="sidc",
        max_trading_volume_per_step=100,
        trade_direction=TradeDirection.SELL_ONLY,
    )
    energy_system = EnergySystem(
        portfolio=portfolio,
        markets=[sdac_market, sidc_market],
        scenarios=[
            StochasticScenario(
                name="scenario_1",
                probability=0.51,
                available_capacity_profiles={
                    "ccgt": 8 * [100],
                },
                market_prices={
                    "sdac": 8 * [200],
                    "sidc": [190, 190, 190, 190, 190, 190, 190, 190],
                },
            ),
            StochasticScenario(
                name="scenario2",
                probability=0.49,
                available_capacity_profiles={
                    "ccgt": 8 * [100],
                },
                market_prices={
                    "sdac": 8 * [200],
                    "sidc": [210, 210, 210, 210, 210, 210, 210, 210],
                },
            ),
        ],
        timestep=timedelta(minutes=30),
        cvar_config=CVaRConfig(
            confidence_level=0.5,
            weight=1,
        ),
        number_of_steps=8,
        power_unit="MW",
    )

    result = energy_system.optimize()
    logger.info(result.termination_condition)
    logger.info(result.solver_status)
    logger.info("generators power")
    logger.info(result.generators.power)
    logger.info("volume sold to markets")
    logger.info(result.markets.sell_volume)
    logger.info(result.markets.buy_volume)
    logger.info("cvar")
    logger.info(result.cvar.value_at_risk)
    logger.info(result.cvar.cvar)
    logger.info(result.cvar.shortfall_per_scenario)
