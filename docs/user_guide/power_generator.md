# PowerGenerator

A `PowerGenerator` represents any dispatchable power source in your energy system -- think gas turbines, diesel generators, or even a simplified solar/wind unit with a fixed capacity.

## Basic usage

```python
from odys.energy_system_models.assets.generator import PowerGenerator

gen = PowerGenerator(
    name="gas_turbine",
    nominal_power=100.0,
    variable_cost=50.0,
)
```

That's really all you need. The optimizer will figure out the dispatch (how much power to produce at each timestep) to minimize total cost while meeting demand.

## Fields

| Field           | Type    | Required | Default | Description                                             |
| --------------- | ------- | -------- | ------- | ------------------------------------------------------- |
| `name`          | `str`   | Yes      | -       | Unique identifier for the generator                     |
| `nominal_power` | `float` | Yes      | -       | Maximum power output (in your chosen power unit)        |
| `variable_cost` | `float` | Yes      | -       | Cost per unit of energy produced (currency/MWh)         |
| `min_power`     | `float` | No       | `0.0`   | Minimum power output when the generator is on           |
| `ramp_up`       | `float` | No       | `None`  | Max increase in power per hour                          |
| `ramp_down`     | `float` | No       | `None`  | Max decrease in power per hour                          |
| `min_up_time`   | `int`   | No       | `1`     | Minimum number of timesteps the generator must stay on  |
| `min_down_time` | `int`   | No       | `1`     | Minimum number of timesteps the generator must stay off |
| `startup_cost`  | `float` | No       | `0.0`   | Cost incurred each time the generator starts up         |
| `shutdown_cost` | `float` | No       | `None`  | Cost incurred each time the generator shuts down        |

## Ramp constraints

If your generator can't change output instantly, set ramp limits:

```python
gen = PowerGenerator(
    name="slow_gen",
    nominal_power=200.0,
    variable_cost=30.0,
    ramp_up=50.0,   # can increase by at most 50 MW/h
    ramp_down=40.0,  # can decrease by at most 40 MW/h
)
```

When `ramp_up` or `ramp_down` is `None` (the default), there's no ramp constraint -- the generator can jump from 0 to full power in a single step.

## Minimum up/down times

These prevent the optimizer from toggling the generator on and off every timestep:

```python
gen = PowerGenerator(
    name="coal_plant",
    nominal_power=500.0,
    variable_cost=25.0,
    min_up_time=4,   # once on, stays on for at least 4 steps
    min_down_time=2,  # once off, stays off for at least 2 steps
)
```

## Startup and shutdown costs

You can penalize switching the generator on or off:

```python
gen = PowerGenerator(
    name="peaker",
    nominal_power=50.0,
    variable_cost=80.0,
    startup_cost=500.0,
    shutdown_cost=100.0,
)
```

This makes the optimizer think twice before toggling the generator, which is realistic for many thermal plants.

## Available capacity profiles

In a `Scenario`, you can limit the generator's available capacity per timestep using `available_capacity_profiles`. This is useful for modeling things like planned maintenance or variable renewable output:

```python
from odys.energy_system_models.scenarios import Scenario

scenario = Scenario(
    available_capacity_profiles={
        "gas_turbine": [100, 100, 50, 50, 100, 100, 100],
    },
    load_profiles={"load": [80, 90, 70, 60, 85, 95, 80]},
)
```

The key in the dict must match the generator's `name`.

## Results

After optimization, access generator results through `result.generators`:

```python
result = energy_system.optimize()

result.generators.power     # dispatch per timestep
result.generators.status    # on/off status (1 or 0)
result.generators.startup   # startup events
result.generators.shutdown  # shutdown events
```

Each of these is a `pandas.DataFrame`.
