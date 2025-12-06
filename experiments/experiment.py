"""Energy system optimization experiment.

This module demonstrates the usage of the odis library for energy system optimization.
It creates a simple energy system with generators and batteries, then optimizes
the system operation to meet demand at minimum cost.
"""

from datetime import timedelta

from odis.energy_system import EnergySystem
from odis.energy_system_models.assets.generator import PowerGenerator
from odis.energy_system_models.assets.load import Load, LoadType
from odis.energy_system_models.assets.portfolio import AssetPortfolio
from odis.energy_system_models.assets.storage import Battery
from odis.energy_system_models.scenarios import Scenario
from odis.utils.logging import get_logger

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
    battery_1 = Battery(
        name="battery1",
        max_power=200.0,
        capacity=100.0,
        efficiency_charging=0.9,
        efficiency_discharging=0.8,
        soc_start=100.0,
        soc_end=50.0,
        soc_min=10.0,
    )
    portfolio = AssetPortfolio()
    portfolio.add_asset(generator_1)
    portfolio.add_asset(generator_2)
    portfolio.add_asset(battery_1)
    load = Load(name="load", type=LoadType.Fixed)
    portfolio.add_asset(load)

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
    battery_results = result.batteries
    logger.info("generators power")
    logger.info(result.generators.power)
    logger.info("battery")
    logger.info(result.batteries.net_power)

    logger.info("results summary dataframe")
    logger.info(result.to_dataframe)
