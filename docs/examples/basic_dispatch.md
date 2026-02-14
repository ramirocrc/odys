# Basic Dispatch

This example shows the core odys workflow: two generators and a battery dispatched to meet a fixed load at minimum cost.

**Source**: [`examples/example1.py`](https://github.com/ramirocrc/odys/blob/main/examples/example1.py)

## What it demonstrates

- Setting up generators with different costs and constraints (ramp rates, min up time, min power)
- Adding a battery with efficiency losses and SOC bounds
- Using `available_capacity_profiles` to limit a generator's output over time
- Reading the optimization results

## The setup

We have two generators with different characteristics:

- **gen1**: Cheap (20 $/MWh), 100 MW, with a ramp-down limit and varying available capacity
- **gen2**: Expensive (100 $/MWh), 150 MW, with ramp limits, min power, and a 4-step min up time

Plus a battery (200 MW, 100 MWh) that starts full and must end at 50% SOC.

## Code

```python
from datetime import timedelta

from odys.energy_system import EnergySystem
from odys.energy_system_models.assets.generator import PowerGenerator
from odys.energy_system_models.assets.load import Load, LoadType
from odys.energy_system_models.assets.portfolio import AssetPortfolio
from odys.energy_system_models.assets.storage import Battery
from odys.energy_system_models.scenarios import Scenario

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
    soc_start=1.0,
    soc_end=0.5,
    soc_min=0.1,
)

portfolio = AssetPortfolio()
portfolio.add_asset(generator_1)
portfolio.add_asset(generator_2)
portfolio.add_asset(battery_1)
portfolio.add_asset(Load(name="load", type=LoadType.Fixed))

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
```

## Reading the results

```python
# Check that the solver found an optimal solution
print(result.solver_status)         # "ok"
print(result.termination_condition)  # "optimal"

# Generator dispatch
print(result.generators.power)

# Battery charge/discharge
print(result.batteries.net_power)

# Everything in one DataFrame
print(result.to_dataframe)
```

## What to look for

- **gen1** is dispatched first because it's cheaper, but it's capped by `available_capacity_profiles` in later timesteps.
- **gen2** kicks in when gen1 can't cover the load, but once it's on, it stays on for at least 4 steps (`min_up_time=4`).
- The **battery** discharges when demand is high and charges when demand is low, respecting its SOC constraints.
