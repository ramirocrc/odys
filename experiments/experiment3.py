"""Energy system optimization experiment.

This module demonstrates the usage of the odys library for energy system optimization.
It creates a simple energy system with generators and batteries, then optimizes
the system operation to meet demand at minimum cost.
"""

from datetime import timedelta

from logging_setup import setup_rich_logging

from odys.energy_system import EnergySystem
from odys.energy_system_models.assets.generator import PowerGenerator
from odys.energy_system_models.assets.load import Load
from odys.energy_system_models.assets.portfolio import AssetPortfolio
from odys.energy_system_models.scenarios import StochasticScenario
from odys.utils.logging import get_logger

setup_rich_logging()
logger = get_logger(__name__)

if __name__ == "__main__":
    generator_1 = PowerGenerator(
        name="gen1",
        nominal_power=100.0,
        variable_cost=200.0,
        min_up_time=1,
        ramp_down=100,
    )
    generator_2 = PowerGenerator(
        name="wind_farm",
        nominal_power=150.0,
        variable_cost=100.0,
    )
    portfolio = AssetPortfolio()
    portfolio.add_asset(generator_1)
    portfolio.add_asset(generator_2)
    portfolio.add_asset(Load(name="load"))

    scenarios = [
        StochasticScenario(
            name="low_wind",
            probability=0.1,
            available_capacity_profiles={
                "gen1": [100, 100, 100, 50, 50, 50, 50],
                "wind_farm": [100, 100, 100, 50, 50, 50, 50],
            },
            load_profiles={
                "load": [180, 180, 150, 50, 80, 90, 95],
            },
        ),
        StochasticScenario(
            name="high_wind",
            probability=0.9,
            available_capacity_profiles={
                "gen1": [100, 100, 100, 50, 50, 50, 50],
                "wind_farm": [150, 150, 100, 50, 50, 50, 50],
            },
            load_profiles={
                "load": [180, 180, 150, 50, 80, 90, 95],
            },
        ),
    ]
    energy_system = EnergySystem(
        portfolio=portfolio,
        timestep=timedelta(minutes=30),
        number_of_steps=7,
        scenarios=scenarios,
        power_unit="MW",
    )

    result = energy_system.optimize()
    logger.info(result.termination_condition)
    logger.info(result.solver_status)
    logger.info("generators power")
    logger.info(result.generators.power)
    logger.info(result.to_dataframe.to_csv("results"))
    logger.info(result.to_dataframe)
