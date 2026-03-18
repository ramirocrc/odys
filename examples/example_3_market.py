"""Energy system optimization example.

This module demonstrates the usage of the odys library for energy system optimization.
It creates a simple energy system with generators and batteries, then optimizes
the system operation to meet demand at minimum cost.
"""

from datetime import timedelta

from odys import AssetPortfolio, EnergySystem, Generator, Load, LoadType, Scenario
from odys.energy_system_models.markets import EnergyMarket, TradeDirection
from odys.utils.logging import get_logger, setup_rich_logging

setup_rich_logging()
logger = get_logger(__name__)

if __name__ == "__main__":
    generator_1 = Generator(
        name="ccgt",
        nominal_power=100,
        variable_cost=50,
    )
    load = Load(name="load", type=LoadType.Fixed)

    market = EnergyMarket(
        name="my_market",
        max_trading_volume_per_step=100,
        trade_direction=TradeDirection.BUY_ONLY,
    )

    portfolio = AssetPortfolio()
    portfolio.add_assets(generator_1)
    portfolio.add_assets(load)

    scenario = Scenario(
        available_capacity_profiles={
            "ccgt": 9 * [100],
        },
        load_profiles={
            "load": 9 * [70],
        },
        market_prices={
            "my_market": [80, 70, 40, 30, 30, 80, 90, 60, 40],
        },
    )
    energy_system = EnergySystem(
        portfolio=portfolio,
        markets=market,
        timestep=timedelta(minutes=30),
        number_of_steps=9,
        scenarios=scenario,
        power_unit="MW",
    )

    result = energy_system.optimize()
    logger.info(result.termination_condition)
    logger.info(result.solver_status)
    logger.info("generators power")
    logger.info(round(result.generators.power))
    logger.info(result.markets.buy_volume)
