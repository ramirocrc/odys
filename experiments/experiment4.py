"""Energy system optimization experiment.

This module demonstrates the usage of the optimes library for energy system optimization.
It creates a simple energy system with generators and batteries, then optimizes
the system operation to meet demand at minimum cost.
"""

from datetime import timedelta

from optimes.energy_system import EnergySystem
from optimes.energy_system_models.assets.generator import PowerGenerator
from optimes.energy_system_models.assets.load import Load, LoadType
from optimes.energy_system_models.assets.portfolio import AssetPortfolio
from optimes.energy_system_models.markets import EnergyMarket
from optimes.energy_system_models.scenarios import Scenario
from optimes.utils.logging import get_logger

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
        markets=EnergyMarket(name="sdac"),
        scenarios=Scenario(
            available_capacity_profiles={
                "gen1": [100, 100, 100, 50, 50, 50, 50],
            },
            load_profiles={"load": [200, 75, 200, 50, 100, 120, 125]},
            market_prices={"sdac": [150, 150, 150, 150, 150, 150, 150]},
        ),
        timestep=timedelta(minutes=30),
        number_of_steps=7,
        power_unit="MW",
    )

    result = energy_system.optimize()
    logger.info(result.termination_condition)
    logger.info(result.solver_status)
    logger.info("generators power")
    logger.info(result.generators.power)
    logger.info("market_traded volume")
    logger.info(result.markets.traded_volume)
