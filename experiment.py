"""Energy system optimization experiment.

This module demonstrates the usage of the optimes library for energy system optimization.
It creates a simple energy system with generators and batteries, then optimizes
the system operation to meet demand at minimum cost.
"""

from datetime import timedelta

from optimes.energy_system.assets.generator import PowerGenerator
from optimes.energy_system.assets.portfolio import AssetPortfolio
from optimes.energy_system.assets.storage import Battery
from optimes.energy_system.energy_system_conditions import EnergySystem
from optimes.optimization.model_optimizer import EnergySystemOptimizer

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
        efficiency_charging=1,
        efficiency_discharging=1,
        soc_initial=100.0,
        soc_terminal=50.0,
    )
    portfolio = AssetPortfolio()
    portfolio.add_asset(generator_1)
    portfolio.add_asset(generator_2)
    portfolio.add_asset(battery_1)

    system_data = EnergySystem(
        portfolio=portfolio,
        demand_profile=[50, 75, 100, 125, 150],
        timestep=timedelta(minutes=30),
    )

    optimizer = EnergySystemOptimizer(system_data)

    result = optimizer.optimize()
    results_df = result.to_dataframe("horizontal")
    results_df.to_csv("final_results.csv")
