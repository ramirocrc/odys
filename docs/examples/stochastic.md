# Stochastic Scenarios

This example shows how to optimize across multiple scenarios with different wind outputs, using generators and a battery.

**Source**: [`examples/example2.py`](https://github.com/ramirocrc/odys/blob/main/examples/example2.py)

## What it demonstrates

- Defining multiple `StochasticScenario` instances with probabilities
- Varying `available_capacity_profiles` across scenarios (different wind conditions)
- How the optimizer balances dispatch decisions across uncertain futures

## The setup

Two generators:

- **gen1**: A conventional generator (100 MW, 200 $/MWh)
- **wind_farm**: A wind generator (150 MW, 100 $/MWh) with variable output

Plus a battery (200 MW, 100 MWh) and a fixed load.

We define two equally likely scenarios:

- **default**: Moderate wind availability
- **high_wind**: More wind available in the first few timesteps

## Code

```python
from datetime import timedelta

from odys.energy_system import EnergySystem
from odys.energy_system_models.assets.generator import PowerGenerator
from odys.energy_system_models.assets.load import Load, LoadType
from odys.energy_system_models.assets.portfolio import AssetPortfolio
from odys.energy_system_models.assets.storage import Battery
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
battery_1 = Battery(
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
            "gen1": [100, 100, 100, 50, 50, 50, 50],
            "wind_farm": [100, 100, 100, 50, 50, 50, 50],
        },
        load_profiles={
            "load": [180, 180, 150, 50, 80, 90, 100],
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
```

## Reading the results

```python
print(result.generators.power)      # dispatch per scenario
print(result.batteries.net_power)    # battery behavior per scenario
print(result.to_dataframe)           # everything combined
```

Since we have two scenarios, the results include a scenario dimension. You can compare how the optimizer dispatches differently under each wind condition.

## What to look for

- The **wind_farm** is cheaper, so the optimizer uses it first. In the high_wind scenario, it can produce more.
- **gen1** is expensive (200 $/MWh) and only runs when the wind farm and battery can't cover the load.
- The **battery** shifts energy across timesteps to minimize total cost, considering both scenarios.
