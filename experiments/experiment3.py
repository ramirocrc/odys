"""Energy system optimization experiment.

This module demonstrates the usage of the optimes library for energy system optimization.
It creates a simple energy system with generators and batteries, then optimizes
the system operation to meet demand at minimum cost.
"""

from datetime import timedelta

from optimes.energy_system import EnergySystem
from optimes.energy_system_models.assets.generator import PowerGenerator
from optimes.energy_system_models.assets.portfolio import AssetPortfolio
from optimes.energy_system_models.scenarios import SctochasticScenario
from optimes.utils.logging import get_logger

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

    scenarios = [
        SctochasticScenario(
            name="low_wind",
            probability=0.1,
            available_capacity_profiles={
                "gen1": [100, 100, 100, 50, 50, 50, 50],
                "wind_farm": [100, 100, 100, 50, 50, 50, 50],
            },
        ),
        SctochasticScenario(
            name="high_wind",
            probability=0.9,
            available_capacity_profiles={
                "gen1": [100, 100, 100, 50, 50, 50, 50],
                "wind_farm": [150, 150, 100, 50, 50, 50, 50],
            },
        ),
    ]
    energy_system = EnergySystem(
        portfolio=portfolio,
        demand_profile=[180, 180, 150, 50, 80, 90, 95],
        timestep=timedelta(minutes=30),
        scenarios=scenarios,
        enforce_non_anticipativity=False,
        power_unit="MW",
    )

    result = energy_system.optimize()
    logger.info(result.termination_condition)
    logger.info(result.solver_status)
    logger.info("generators power")
    logger.info(result.generators.power)
    logger.info(result.to_dataframe.to_csv("results"))
