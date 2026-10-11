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

At the first step, $p_{g,-1}$ and $u_{g,-1}$ come from the generator's [initial state](#initial-and-final-state).

## Fields

| Field           | Type    | Required | Default | Description                                             |
| --------------- | ------- | -------- | ------- | ------------------------------------------------------- |
| `name`          | `str`   | Yes      | -       | Unique identifier for the generator                     |
| `nominal_power` | `float` | Yes      | -       | Maximum power output (in your chosen power unit)        |
| `variable_cost` | `float` | Yes      | -       | Cost per unit of energy produced (currency/MWh)         |
| `min_power`     | `float` | No       | `0.0`   | Minimum power output when the generator is on           |
| `ramp_up`       | `float` | No       | `None`  | Max increase in power per hour                          |
| `ramp_down`     | `float` | No       | `None`  | Max decrease in power per hour                          |
| `min_up_time`   | `timedelta \| None` | No | `None` | Minimum time the generator stays on once started  |
| `min_down_time` | `timedelta \| None` | No | `None` | Minimum time the generator stays off once stopped |
| `startup_cost`  | `float` | No       | `0.0`   | Cost incurred each time the generator starts up         |
| `shutdown_cost` | `float` | No       | `0.0`   | Cost incurred each time the generator shuts down         |

`min_up_time` and `min_down_time` must be a whole number of timesteps. With 15-minute steps, `timedelta(minutes=45)` works, but `timedelta(minutes=50)` raises an `OdysValidationError` when the `EnergySystem` is created.

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

Ramp limits also apply at the first step, measured from the generator's [initial state](#initial-and-final-state), so a generator with ramp limits needs one.

Odys has no separate startup or shutdown ramp rate. A generator whose `ramp_up` is below its `min_power` can never start, at the first step or later, because going from 0 MW to `min_power` breaks the ramp limit. Likewise, a generator whose `ramp_down` is below its output cannot shut down in one step.

## Minimum up time

Once a generator starts, it must stay on for at least `min_up_time`:

```python
from datetime import timedelta

gen = Generator(
    name="coal_plant",
    nominal_power=500.0,
    variable_cost=25.0,
    min_up_time=timedelta(hours=4),  # once on, stays on for at least 4 hours
)
```

Before each shutdown, the optimizer counts the steps on in a rolling window of $U_g$ steps, where $U_g$ is the minimum up time in steps. Time on before the horizon counts too. $H^{up}_{g,t}$ is the number of the window's steps before $t=0$ during which the generator was already on, taken from its [initial state](#initial-and-final-state):

$$
\sum_{\tau=\max(0,\,t-U_g+1)}^{t} u_{g,\tau} + H^{up}_{g,t} \ge U_g y^{shutdown}_{g,t+1},
\qquad H^{up}_{g,t} = u^0_g \min\big(T^0_g, \max(0, U_g - 1 - t)\big)
$$

A generator that has been on for less than its minimum up time also cannot shut down at the first step: $y^{shutdown}_{g,0} = 0$ when $u^0_g = 1$ and $T^0_g < U_g$.

## Minimum down time

Once a generator stops, it must stay off for at least `min_down_time`:

```python
gen = Generator(
    name="coal_plant",
    nominal_power=500.0,
    variable_cost=25.0,
    min_down_time=timedelta(hours=3),  # once off, stays off for at least 3 hours
)
```

The rolling constraint mirrors the one for minimum up time. $D_g$ is the minimum down time in steps, and $H^{down}_{g,t}$ is the number of the window's steps before $t=0$ during which the generator was off:

$$
\sum_{\tau=\max(0,\,t-D_g+1)}^{t} (1 - u_{g,\tau}) + H^{down}_{g,t} \ge D_g y^{start}_{g,t+1},
\qquad H^{down}_{g,t} = (1 - u^0_g) \min\big(T^0_g, \max(0, D_g - 1 - t)\big)
$$

A generator that has been off for less than its minimum down time cannot start at the first step: $y^{start}_{g,0} = 0$ when $u^0_g = 0$ and $T^0_g < D_g$.

## Startup cost and shutdown cost

Both startup and shutdown cost are included in the objective.

```python
gen = Generator(
    name="peaker",
    nominal_power=50.0,
    variable_cost=80.0,
    startup_cost=500.0,
    shutdown_cost=200.0,
)
```

This makes the optimizer think twice before turning the generator on or off, which is realistic for many thermal plants. The optimizer weighs these costs against the benefit of running.

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

At $t=0$, $u_{g,-1} = u^0_g$, so a generator that is already on pays no startup cost for running at the first step.

## Initial and final state

Most studies don't start from scratch: a plant that ran yesterday is still on this morning. Tell the optimizer where each generator starts with a `GeneratorInitialState`, and pass it to the [EnergySystem](energy_system.md):

```python
from datetime import timedelta

from odys import (
    AssetPortfolio,
    EnergySystem,
    FixedLoad,
    Generator,
    GeneratorFinalState,
    GeneratorInitialState,
    LoadProfile,
    Scenario,
)

ccgt = Generator(
    name="ccgt",
    nominal_power=400.0,
    min_power=150.0,
    variable_cost=45.0,
    ramp_up=100.0,
    min_up_time=timedelta(hours=4),
)
load = FixedLoad(name="demand")

energy_system = EnergySystem(
    portfolio=AssetPortfolio([ccgt, load]),
    timestep=timedelta(hours=1),
    number_of_steps=4,
    scenarios=Scenario(profiles=(LoadProfile(load=load, values=[300, 350, 250, 200]),)),
    initial_conditions=(GeneratorInitialState(generator=ccgt, power=250.0, time_in_state=timedelta(hours=2)),),
    final_conditions=(GeneratorFinalState(generator=ccgt, power=200.0),),
)
```

Here the CCGT has been producing 250 MW for 2 hours. That means:

- it can ramp to at most 350 MW at the first step;
- it must stay on for 2 more hours to complete its 4-hour minimum up time;
- it pays no startup cost;
- it must end at 200 MW.

| Class                   | Field           | Type                | Description                                                                   |
| ----------------------- | --------------- | ------------------- | ----------------------------------------------------------------------------- |
| `GeneratorInitialState` | `generator`     | `Generator`         | The generator this state belongs to                                           |
|                         | `power`         | `float`             | Output just before the first step: 0 (off) or between `min_power` and `nominal_power` |
|                         | `time_in_state` | `timedelta \| None` | How long it has been on (`power > 0`) or off (`power = 0`)                    |
| `GeneratorFinalState`   | `generator`     | `Generator`         | The generator this state belongs to                                           |
|                         | `power`         | `float`             | Output at the last step: 0 (off) or between `min_power` and `nominal_power`   |

The status comes from the power: a generator at 0 MW is off, and any other output means it is on.

A `GeneratorInitialState` is **required** when a generator's results depend on its starting state. That's the case when it has `ramp_up`, `ramp_down`, `min_up_time`, `min_down_time`, `startup_cost` or `shutdown_cost` set; odys never guesses the starting state. A generator without these parameters needs no initial state and starts off.

`time_in_state` is required when the matching minimum time is set: `min_up_time` for a generator that starts on, `min_down_time` for one that starts off. It must be a whole number of timesteps.

A final state fixes the output at the last step:

$$
p_{g,T-1} = p^{end}_g
$$

The final output must fit the generator's available capacity at the last step in every scenario. An exact final output combined with ramp limits can make the problem infeasible, so give the generator enough steps to reach it.

See [Initial and final conditions](initial_and_final_conditions.md) for every asset type.

## Available capacity profiles

In a `Scenario`, you can limit the generator's available capacity per timestep with an `AvailableCapacityProfile`. This is useful for modeling things like planned maintenance or variable renewable output:

```python
from odys import AvailableCapacityProfile, LoadProfile, FixedLoad, Generator, Scenario

gen = Generator(name="gas_turbine", nominal_power=100.0, variable_cost=50.0)
load = FixedLoad(name="load")

scenario = Scenario(
    profiles=(
        AvailableCapacityProfile(generator=gen, values=[100, 100, 50, 50, 100, 100, 100]),
        LoadProfile(load=load, values=[80, 90, 70, 60, 85, 95, 80]),
    ),
)
```

The profile references the generator object, and each value must lie between 0 and its `nominal_power`; otherwise building the profile raises an `OdysValidationError`.

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

Each of these is a `pandas.Series` indexed by generator and time (and scenario, when there is more than one).

## Next steps

Next, see how [Load](load.md) defines the demand your system must serve, or jump to [StationaryStorage](storage.md) to add batteries.
