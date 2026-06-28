---
icon: fontawesome/solid/bolt
---

# Generator

A `Generator` represents any dispatchable power source in your energy system -- think gas turbines, diesel generators, or even a simplified solar/wind unit with a fixed capacity.

See [Mathematical notation](mathematical_notation.md) for the full list of symbols used below.

## Basic usage

Let's create a generator.

```python
from odys import Generator

gen = Generator(
    name="gas_turbine",
    nominal_power=100.0,
    variable_cost=50.0,
)
```

That's really all you need. The optimizer will figure out the dispatch (how much power to produce at each timestep) to minimize total cost while meeting demand.

In the model, that dispatch is bounded by:

$$
0 \le p_{g,t}, \qquad u_{g,t} \in \{0,1\}
$$

$$
p_{g,t} - P^{\max}_g u_{g,t} \le 0
$$

$$
p_{g,t} \ge \epsilon_g u_{g,t}, \qquad p_{g,t} \ge P^{\min}_g u_{g,t}
$$

and, when enabled, by ramp limits:

$$
p_{g,t} - p_{g,t-1} \le R^{up}_g, \qquad p_{g,t-1} - p_{g,t} \le R^{down}_g
$$

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
| `min_down_time` | `int`   | No       | `1`     | Accepted by the model object, but not enforced by the current optimization constraints |
| `startup_cost`  | `float` | No       | `0.0`   | Cost incurred each time the generator starts up         |
| `shutdown_cost` | `float` | No       | `None`  | Accepted by the model object, but not included in the current objective |

## Ramp constraints

If your generator can't change output instantly, set ramp limits. Real thermal plants can't jump from zero to full power in a single step -- they need time to ramp up.

```python
gen = Generator(
    name="slow_gen",
    nominal_power=200.0,
    variable_cost=30.0,
    ramp_up=50.0,  # can increase by at most 50 MW/h
    ramp_down=40.0,  # can decrease by at most 40 MW/h
)
```

When `ramp_up` or `ramp_down` is `None` (the default), there's no ramp constraint -- the generator can jump from 0 to full power in a single step. Use this for fast-responding assets or when ramp limits don't matter for your study.

## Minimum up time

The current optimization model enforces minimum up time with a rolling constraint tied to shutdown events:

$$
\sum_{\tau=t-U_g+1}^{t} u_{g,\tau} \ge U_g y^{shutdown}_{g,t+1}
$$

where $U_g$ is the minimum up time.

```python
gen = Generator(
    name="coal_plant",
    nominal_power=500.0,
    variable_cost=25.0,
    min_up_time=4,  # once on, stays on for at least 4 steps
)
```

## Startup cost and shutdown tracking

Startup cost is included in the objective. Shutdown events are tracked as decision variables, but `shutdown_cost` is not currently included in the objective.

```python
gen = Generator(
    name="peaker",
    nominal_power=50.0,
    variable_cost=80.0,
    startup_cost=500.0,
)
```

This makes the optimizer think twice before turning the generator on, which is realistic for many thermal plants. Notice how the startup cost creates a tradeoff: the optimizer weighs the cost of starting up against the benefit of running.

Startup and shutdown are represented with binary transition variables:

$$
y^{start}_{g,t} \ge u_{g,t} - u_{g,t-1}
$$

$$
y^{start}_{g,t} \le u_{g,t}, \qquad y^{start}_{g,t} + u_{g,t-1} \le 1
$$

$$
y^{shutdown}_{g,t} \ge u_{g,t-1} - u_{g,t}
$$

$$
y^{shutdown}_{g,t} \le u_{g,t-1}, \qquad y^{shutdown}_{g,t} + u_{g,t} \le 1
$$

## Available capacity profiles

In a `Scenario`, you can limit the generator's available capacity per timestep using `available_capacity_profiles`. This is useful for modeling things like planned maintenance or variable renewable output:

```python
from odys import Scenario

scenario = Scenario(
    available_capacity_profiles={
        "gas_turbine": [100, 100, 50, 50, 100, 100, 100],
    },
    load_profiles={"load": [80, 90, 70, 60, 85, 95, 80]},
)
```

The key in the dict must match the generator's `name`.

The implemented constraint is:

$$
p_{g,t,s} \le A_{g,t,s}
$$

## Results

After optimization, access generator results through `result.generators`:

```python
result = energy_system.optimize()

result.generators.power  # dispatch per timestep
result.generators.status  # on/off status (1 or 0)
result.generators.startup  # startup events
result.generators.shutdown  # shutdown events
```

Each of these is a `pandas.DataFrame`.

## Next steps

Next, see how [Load](load.md) defines the demand your system must serve.
