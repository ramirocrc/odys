"""Energy system optimization example.

This module demonstrates the usage of the odys library for energy system optimization.
It creates a simple energy system with generators and batteries, then optimizes
the system operation to meet demand at minimum cost.
"""

from datetime import timedelta

from odys import AssetPortfolio, EnergySystem, Generator, Load, LoadType, Scenario, Storage
from odys.utils.logging import get_logger, setup_rich_logging

setup_rich_logging()
logger = get_logger(__name__)

if __name__ == "__main__":
    generator_1 = Generator(
        name="gen1",
        nominal_power=100.0,
        variable_cost=20.0,
        min_up_time=1,
        ramp_down=100,
    )
    generator_2 = Generator(
        name="gen2",
        nominal_power=150.0,
        variable_cost=100.0,
        min_up_time=4,
        min_power=30,
        startup_cost=0,
        ramp_up=140,
        ramp_down=100,
    )
    battery_1 = Storage(
        name="battery1",
        max_power=200.0,
        capacity=100.0,
        efficiency_charging=0.9,
        efficiency_discharging=0.8,
        soc_start=1.0,
        soc_end=0.5,
        soc_min=0.1,
    )
    portfolio = AssetPortfolio()
    portfolio.add_assets(generator_1)
    portfolio.add_assets(generator_2)
    portfolio.add_assets(battery_1)
    load = Load(name="load", type=LoadType.Fixed)
    portfolio.add_assets(load)

    energy_system = EnergySystem(
        portfolio=portfolio,
        scenarios=Scenario(
            available_capacity_profiles={
                "gen1": [100, 100, 100, 50, 50, 50, 50],
            },
            load_profiles={"load": [300, 75, 300, 50, 100, 120, 125]},
        ),
        timestep=timedelta(minutes=30),
        number_of_steps=7,
        power_unit="MW",
    )

    result = energy_system.optimize()
    logger.info(result.termination_condition)
    logger.info(result.solver_status)
    battery_results = result.storages
    logger.info("generators power")
    logger.info(result.generators.power)
    logger.info("battery")
    logger.info(result.storages.net_power)

    logger.info("results summary dataframe")
    logger.info(result.to_dataframe())
