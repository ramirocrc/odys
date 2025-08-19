"""Energy system optimization experiment.

This module demonstrates the usage of the optimes library for energy system optimization.
It creates a simple energy system with generators and batteries, then optimizes
the system operation to meet demand at minimum cost.
"""

from datetime import timedelta

from optimes.energy_system import EnergySystem
from optimes.energy_system_models.assets.generator import PowerGenerator
from optimes.energy_system_models.assets.portfolio import AssetPortfolio
from optimes.energy_system_models.assets.storage import Battery
from optimes.utils.logging import get_logger

logger = get_logger(__name__)

if __name__ == "__main__":
    generator_1 = PowerGenerator(
        name="gen1",
        nominal_power=100.0,
        variable_cost=20.0,
    )
    generator_2 = PowerGenerator(
        name="gen2",
        nominal_power=150.0,
        variable_cost=25.0,
    )
    battery_1 = Battery(
        name="battery1",
        max_power=200.0,
        capacity=100.0,
        efficiency_charging=0.9,
        efficiency_discharging=0.8,
        soc_initial=100.0,
        soc_terminal=50.0,
    )
    portfolio = AssetPortfolio()
    portfolio.add_asset(generator_1)
    portfolio.add_asset(generator_2)
    portfolio.add_asset(battery_1)

    energy_system = EnergySystem(
        portfolio=portfolio,
        demand_profile=[50, 75, 100, 125, 150],
        timestep=timedelta(minutes=30),
    )

    result = energy_system.optimize()
    results_df = result.to_dataframe("basic")
    logger.info(results_df)
