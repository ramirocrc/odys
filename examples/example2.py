"""Energy system optimization example.

This module demonstrates the usage of the odys library for energy system optimization.
It creates a simple energy system with generators and batteries, then optimizes
the system operation to meet demand at minimum cost.
"""

from datetime import timedelta

from odys import AssetPortfolio, EnergySystem, Generator, Load, LoadType, StochasticScenario, Storage
from odys.utils.logging import get_logger, setup_rich_logging

setup_rich_logging()
logger = get_logger(__name__)

if __name__ == "__main__":
    generator_1 = Generator(
        name="ccgt",
        nominal_power=100,
        variable_cost=200,
        min_up_time=1,
        ramp_down=100,
    )
    generator_2 = Generator(
        name="solar_pv",
        nominal_power=150,
        variable_cost=0,
    )
    battery_1 = Storage(
        name="battery1",
        max_power=200.0,
        capacity=100,
        efficiency_charging=0.9,
        efficiency_discharging=0.8,
        soc_start=1.0,
        soc_end=0.5,
    )
    load = Load(name="load", type=LoadType.Fixed)
    portfolio = AssetPortfolio()
    portfolio.add_asset(generator_1)
    portfolio.add_asset(generator_2)
    portfolio.add_asset(battery_1)
    portfolio.add_asset(load)

    scenarios = [
        StochasticScenario(
            name="default",
            probability=0.5,
            available_capacity_profiles={
                "ccgt": [100, 100, 100, 100, 100, 100, 100],
                "solar_pv": [0, 20, 40, 60, 40, 20, 0],
            },
            load_profiles={
                "load": [80, 80, 80, 80, 80, 80, 80],
            },
        ),
        StochasticScenario(
            name="high_wind",
            probability=0.5,
            available_capacity_profiles={
                "gen1": [100, 100, 100, 50, 50, 50, 50],
                "wind_farm": [150, 150, 100, 50, 50, 50, 50],
            },
            load_profiles={
                "load": [180, 180, 150, 50, 80, 90, 100],
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
    battery_results = result.storages
    logger.info("generators power")
    logger.info(result.generators.power)
    logger.info("battery net power")
    logger.info(result.storages.net_power)

    logger.info(result.to_dataframe())
