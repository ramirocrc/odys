"""
Optimes - Python framework for optimizing multi-energy systems.

This package provides tools for modeling and optimizing energy systems with generators,
batteries, and other energy assets using mathematical optimization techniques.

Example:
    >>> from optimes.energy_system.assets.generator import PowerGenerator
    >>> from optimes.energy_system.assets.storage import Battery
    >>> from optimes.energy_system.assets.portfolio import AssetPortfolio
    >>> from optimes.energy_system.energy_system_conditions import EnergySystem
    >>> from optimes.optimization.model_optimizer import EnergySystemOptimizer
    >>>
    >>> # Create assets
    >>> generator = PowerGenerator(name="gen1", nominal_power=100.0, variable_cost=20.0)
    >>> battery = Battery(name="battery1", max_power=50.0, capacity=100.0,
    ...                  efficiency_charging=0.9, efficiency_discharging=0.9,
    ...                  soc_initial=50.0)
    >>>
    >>> # Build portfolio and system
    >>> portfolio = AssetPortfolio()
    >>> portfolio.add_asset(generator)
    >>> portfolio.add_asset(battery)
    >>>
    >>> system = EnergySystem(
    ...     portfolio=portfolio,
    ...     demand_profile=[80, 100, 120, 90, 70],
    ...     timestep=timedelta(hours=1)
    ... )
    >>>
    >>> # Optimize
    >>> optimizer = EnergySystemOptimizer(system)
    >>> results = optimizer.optimize()
    >>> print(results.to_dataframe)
"""

from datetime import timedelta

from optimes.energy_system.assets.generator import PowerGenerator
from optimes.energy_system.assets.portfolio import AssetPortfolio
from optimes.energy_system.assets.storage import Battery
from optimes.energy_system.energy_system_conditions import EnergySystem
from optimes.optimization.model_optimizer import EnergySystemOptimizer
from optimes.optimization.optimization_results import OptimizationResults

__version__ = "0.0.1"
__author__ = "Ramiro Criach"
__email__ = "ramirocriach@gmail.com"

__all__ = [
    "AssetPortfolio",
    "Battery",
    "EnergySystem",
    "EnergySystemOptimizer",
    "OptimizationResults",
    "PowerGenerator",
    "timedelta",
]
