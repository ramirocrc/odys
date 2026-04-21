"""Example 1: Basic dispatch optimization."""

from datetime import timedelta

from odys import AssetPortfolio, EnergySystem, Generator, Load, LoadType, Scenario
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
    portfolio = AssetPortfolio([generator_1, generator_2, load])

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
    )

    result = energy_system.optimize()
    logger.info("Generators optimal dispatch")
    for gen_dispatch in result.generators:
        logger.info(gen_dispatch.name)
        logger.info(gen_dispatch.to_dataframe())

    logger.info(result.to_dataset())
