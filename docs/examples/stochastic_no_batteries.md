# Stochastic Without Batteries

This example shows stochastic optimization with generators only -- no battery storage.

**Source**: [`examples/example3.py`](https://github.com/ramirocrc/odys/blob/main/examples/example3.py)

## What it demonstrates

- Stochastic dispatch without energy storage
- How asymmetric probabilities (10% vs 90%) affect the optimal solution
- A simpler system where generators must directly meet demand at each timestep

## The setup

Two generators:

- **gen1**: Conventional (100 MW, 200 $/MWh) with a ramp-down limit
- **wind_farm**: Wind-based (150 MW, 100 $/MWh) with variable availability

No battery this time -- the generators have to handle everything.

Two scenarios with asymmetric probabilities:

- **low_wind** (10%): Moderate wind availability
- **high_wind** (90%): More wind in the first few timesteps

## Code

```python
from datetime import timedelta

from odys.energy_system import EnergySystem
from odys.energy_system_models.assets.generator import PowerGenerator
from odys.energy_system_models.assets.load import Load
from odys.energy_system_models.assets.portfolio import AssetPortfolio
from odys.energy_system_models.scenarios import StochasticScenario

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
portfolio.add_asset(Load(name="load"))

scenarios = [
    StochasticScenario(
        name="low_wind",
        probability=0.1,
        available_capacity_profiles={
            "gen1": [100, 100, 100, 50, 50, 50, 50],
            "wind_farm": [100, 100, 100, 50, 50, 50, 50],
        },
        load_profiles={
            "load": [180, 180, 150, 50, 80, 90, 95],
        },
    ),
    StochasticScenario(
        name="high_wind",
        probability=0.9,
        available_capacity_profiles={
            "gen1": [100, 100, 100, 50, 50, 50, 50],
            "wind_farm": [150, 150, 100, 50, 50, 50, 50],
        },
        load_profiles={
            "load": [180, 180, 150, 50, 80, 90, 95],
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
```

## Reading the results

```python
print(result.generators.power)
print(result.to_dataframe)
```

## What to look for

- With 90% probability on high wind, the optimizer leans heavily toward the wind scenario.
- Without a battery, there's no way to shift energy across timesteps -- each step has to balance on its own.
- Compare this to the [Stochastic Scenarios](stochastic.md) example to see how a battery changes the solution.
