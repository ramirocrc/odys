"""Energy system optimization example.

This module demonstrates the usage of the odys library for energy system optimization.
It creates a simple energy system with generators and batteries, then optimizes
the system operation to meet demand at minimum cost.
"""

from datetime import timedelta

from odys import AssetPortfolio, EnergySystem, Generator, Load, LoadType, Scenario
from odys.energy_system_models.assets.storage import Storage
from odys.utils.logging import get_logger, setup_rich_logging

setup_rich_logging()
logger = get_logger(__name__)

if __name__ == "__main__":
    generator_1 = Generator(
        name="ccgt",
        nominal_power=100,
        variable_cost=50,
    )
    generator_2 = Generator(
        name="solar_pv",
        nominal_power=150,
        variable_cost=0,
    )
    load = Load(name="load", type=LoadType.Fixed)

    battery = Storage(
        name="battery",
        capacity=100,
        max_power=200,
        soc_start=0,
        soc_end=0,
    )
    portfolio = AssetPortfolio()
    portfolio.add_asset(generator_1)
    portfolio.add_asset(generator_2)
    portfolio.add_asset(load)
    portfolio.add_asset(battery)

    scenario = Scenario(
        available_capacity_profiles={
            "ccgt": 9 * [100],
            "solar_pv": [0, 30, 60, 80, 100, 80, 60, 30, 0],
        },
        load_profiles={
            "load": 9 * [70],
        },
    )
    energy_system = EnergySystem(
        portfolio=portfolio,
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
    logger.info("battery")
    logger.info(result.storages.net_power)
    logger.info(round(result.storages.state_of_charge, 2))
