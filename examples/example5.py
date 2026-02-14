"""Energy system optimization example.

This module demonstrates the usage of the odys library for energy system optimization.
It creates a simple energy system with generators and batteries, then optimizes
the system operation to meet demand at minimum cost.
"""

from datetime import timedelta

from odys.energy_system import EnergySystem
from odys.energy_system_models.assets.generator import PowerGenerator
from odys.energy_system_models.assets.load import Load, LoadType
from odys.energy_system_models.assets.portfolio import AssetPortfolio
from odys.energy_system_models.markets import EnergyMarket, TradeDirection
from odys.energy_system_models.scenarios import StochasticScenario
from odys.utils.logging import get_logger, setup_rich_logging

setup_rich_logging()
logger = get_logger(__name__)

if __name__ == "__main__":
    generator_1 = PowerGenerator(
        name="gen1",
        nominal_power=100.0,
        variable_cost=20.0,
        min_up_time=1,
        ramp_down=100,
    )
    generator_2 = PowerGenerator(
        name="gen2",
        nominal_power=150.0,
        variable_cost=100.0,
        min_up_time=4,
        min_power=30,
        startup_cost=0,
        ramp_up=140,
        ramp_down=100,
    )
    portfolio = AssetPortfolio()

    portfolio.add_asset(generator_1)
    portfolio.add_asset(generator_2)
    load = Load(name="load", type=LoadType.Fixed)
    portfolio.add_asset(load)

    energy_system = EnergySystem(
        portfolio=portfolio,
        markets=(
            EnergyMarket(
                name="sdac",
                max_trading_volume_per_step=150,
                stage_fixed=True,
                trade_direction=TradeDirection.BUY,
            ),
            EnergyMarket(name="sidc1", max_trading_volume_per_step=100, trade_direction=TradeDirection.BUY),
            EnergyMarket(name="sidc2", max_trading_volume_per_step=50, trade_direction=TradeDirection.BUY),
        ),
        scenarios=[
            StochasticScenario(
                name="scenario1",
                probability=0.5,
                available_capacity_profiles={
                    "gen1": [100, 100, 100, 50, 50, 50, 50],
                },
                load_profiles={"load": [200, 75, 200, 50, 100, 120, 125]},
                market_prices={
                    "sdac": [150, 150, 150, 150, 150, 150, 150],
                    "sidc1": [200, 200, 200, 175, 100, 100, 100],
                    "sidc2": [190, 150, 150, 175, 100, 100, 100],
                },
            ),
            StochasticScenario(
                name="scenario2",
                probability=0.5,
                available_capacity_profiles={
                    "gen1": [100, 100, 100, 50, 50, 50, 50],
                },
                load_profiles={"load": [200, 75, 200, 50, 100, 120, 125]},
                market_prices={
                    "sdac": [210, 210, 210, 185, 100, 100, 100],
                    "sidc1": [120, 140, 140, 140, 140, 140, 140],
                    "sidc2": [200, 160, 140, 180, 110, 90, 100],
                },
            ),
        ],
        timestep=timedelta(minutes=30),
        number_of_steps=7,
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
    logger.info(result.to_dataframe())
