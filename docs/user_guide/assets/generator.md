---
icon: fontawesome/solid/bolt
---

# Generator

A `Generator` represents any dispatchable power source in your energy system -- think gas turbines, diesel generators, or even a simplified solar/wind unit with a fixed capacity.

The optimizer decides how much power each generator produces at every timestep, and whether it is on or off, to maximize profit while meeting demand.

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

## Fields

| Field           | Type            | Required | Default | Description                                             |
| --------------- | --------------- | -------- | ------- | ------------------------------------------------------- |
| `name`          | `str`           | Yes      | -       | Unique identifier for the generator                     |
| `nominal_power` | `float`         | Yes      | -       | Maximum power output (in your chosen power unit)        |
| `variable_cost` | `float`         | Yes      | -       | Cost per unit of energy produced (currency/MWh)         |
| `min_power`     | `float`         | No       | `0.0`   | Minimum power output when the generator is on           |
| `ramp_up`       | `float \| None` | No       | `None`  | Max increase in power from one timestep to the next     |
| `ramp_down`     | `float \| None` | No       | `None`  | Max decrease in power from one timestep to the next     |
| `min_up_time`   | `timedelta \| None` | No   | `None`  | Minimum time the generator stays on once started        |
| `min_down_time` | `timedelta \| None` | No   | `None`  | Minimum time the generator stays off once stopped       |
| `startup_cost`  | `float`         | No       | `0.0`   | Cost incurred each time the generator starts up         |
| `shutdown_cost` | `float`         | No       | `0.0`   | Cost incurred each time the generator shuts down        |

## Minimum power

When a generator is on, it must produce at least `min_power`. When it is off, it produces nothing. This models thermal plants that cannot run stably below a technical minimum.

```python
gen = Generator(
    name="ccgt",
    nominal_power=400.0,
    variable_cost=45.0,
    min_power=150.0,  # either off, or between 150 and 400 MW
)
```

See the [formulation](#math-power-limits).

## Ramp limits

If your generator can't change output instantly, set ramp limits. Real thermal plants can't jump from zero to full power in a single step -- they need time to ramp up.

```python
gen = Generator(
    name="slow_gen",
    nominal_power=200.0,
    variable_cost=30.0,
    ramp_up=50.0,  # can increase by at most 50 MW per step
    ramp_down=40.0,  # can decrease by at most 40 MW per step
)
```

When `ramp_up` or `ramp_down` is `None` (the default), there's no ramp constraint -- the generator can jump from 0 to full power in a single step. Use this for fast-responding assets or when ramp limits don't matter for your study.

Ramp limits also apply at the first step, measured from the generator's [initial state](#initial-and-final-state), so a generator with ramp limits needs one.

Odys has no separate startup or shutdown ramp rate. A generator whose `ramp_up` is below its `min_power` can never start, at the first step or later, because going from 0 MW to `min_power` breaks the ramp limit. Likewise, a generator whose `ramp_down` is below its output cannot shut down in one step.

See the [formulation](#math-ramp-limits).

## Minimum up and down time

`min_up_time` keeps a generator on for at least that many timesteps once it starts. `min_down_time` keeps it off for at least that many timesteps once it stops.

```python
from datetime import timedelta

gen = Generator(
    name="coal_plant",
    nominal_power=500.0,
    variable_cost=25.0,
    min_up_time=timedelta(hours=4),  # once on, stays on for at least 4 hours
    min_down_time=timedelta(hours=3),  # once off, stays off for at least 3 hours
)
```

Both must be a whole number of timesteps. With 15-minute steps, `timedelta(minutes=45)` works, but `timedelta(minutes=50)` raises an `OdysValidationError` when the `EnergySystem` is created.

Time spent on or off before the horizon counts too: a generator that has been on for 1 hour with a 3-hour `min_up_time` must stay on for 2 more hours. That time comes from its [initial state](#initial-and-final-state).

See the [formulation](#math-min-up-down-time).

## Startup and shutdown cost

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

Startups and shutdowns are counted from the generator's [initial state](#initial-and-final-state), so a generator that is already on pays no startup cost for running at the first step.

See the [formulation](#math-startup-shutdown).

## Initial and final state

Most studies don't start from scratch: a plant that ran yesterday is still on this morning. Tell the optimizer where each generator starts with a `GeneratorInitialState`, and pass it to the [EnergySystem](../concepts/energy_system.md):

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

| Class                   | Field           | Type                | Description                                                                           |
| ----------------------- | --------------- | ------------------- | ------------------------------------------------------------------------------------- |
| `GeneratorInitialState` | `generator`     | `Generator`         | The generator this state belongs to                                                   |
|                         | `power`         | `float`             | Output just before the first step: 0 (off) or between `min_power` and `nominal_power` |
|                         | `time_in_state` | `timedelta \| None` | How long it has been on (`power > 0`) or off (`power = 0`)                            |
| `GeneratorFinalState`   | `generator`     | `Generator`         | The generator this state belongs to                                                   |
|                         | `power`         | `float`             | Output at the last step: 0 (off) or between `min_power` and `nominal_power`           |

The status comes from the power: a generator at 0 MW is off, and any other output means it is on.

A `GeneratorInitialState` is **required** when a generator's results depend on its starting state. That's the case when it has `ramp_up`, `ramp_down`, `min_up_time`, `min_down_time`, `startup_cost` or `shutdown_cost` set; odys never guesses the starting state. A generator without these parameters needs no initial state and starts off.

`time_in_state` is required when the matching minimum time is set: `min_up_time` for a generator that starts on, `min_down_time` for one that starts off. It must be a whole number of timesteps. Leave it out otherwise; the generator then counts as having been in its state long enough.

The final output must fit the generator's available capacity at the last step in every scenario. An exact final output combined with ramp limits can make the problem infeasible, so give the generator enough steps to reach it.

See [Initial and final conditions](../concepts/initial_and_final_conditions.md) for every asset type, and the [formulation](#math-initial-final-state).

## Profiles

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

The profile references the generator object, and each value must lie between 0 and its `nominal_power`; otherwise building the profile raises an `OdysValidationError`. A generator without an `AvailableCapacityProfile` can produce up to its `nominal_power`.

See the [formulation](#math-available-capacity).

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

## Mathematical formulation

See [Mathematical notation](../mathematical_notation.md) for every symbol.

### Variables

| Symbol | Result attribute | Domain | Meaning |
| ------ | ---------------- | ------ | ------- |
| $p_{g,t,s}$ | `power` | $\ge 0$ | Power output |
| $u_{g,t,s}$ | `status` | $\{0,1\}$ | 1 when the generator is on |
| $y^{start}_{g,t,s}$ | `startup` | $\{0,1\}$ | 1 when the generator starts at $t$ |
| $y^{shutdown}_{g,t,s}$ | `shutdown` | $\{0,1\}$ | 1 when the generator stops at $t$ |

### Constraints

#### Power limits {#math-power-limits}

$$
p_{g,t,s} \le P^{\max}_g u_{g,t,s}, \qquad p_{g,t,s} \ge P^{\min}_g u_{g,t,s}, \qquad p_{g,t,s} \ge \epsilon_g u_{g,t,s}
$$

where $\epsilon_g = 10^{-5} P^{\max}_g$ makes sure that $u_{g,t,s} = 1$ means the generator actually produces.

#### Ramp limits {#math-ramp-limits}

$$
p_{g,t,s} - p_{g,t-1,s} \le R^{up}_g, \qquad p_{g,t-1,s} - p_{g,t,s} \le R^{down}_g
$$

At the first step, the previous output is the initial output: $p_{g,-1,s} = p^0_g$. When a ramp limit is not set, it defaults to $P^{\max}_g$, which never binds.

#### Startup and shutdown {#math-startup-shutdown}

$$
y^{start}_{g,t,s} \ge u_{g,t,s} - u_{g,t-1,s}, \qquad
y^{start}_{g,t,s} \le u_{g,t,s}, \qquad
y^{start}_{g,t,s} + u_{g,t-1,s} \le 1
$$

$$
y^{shutdown}_{g,t,s} \ge u_{g,t-1,s} - u_{g,t,s}, \qquad
y^{shutdown}_{g,t,s} \le u_{g,t-1,s}, \qquad
y^{shutdown}_{g,t,s} + u_{g,t,s} \le 1
$$

At the first step, the previous status is the initial status: $u_{g,-1,s} = u^0_g$, which is 1 when $p^0_g > 0$. A generator without an initial state starts off.

#### Minimum up and down time {#math-min-up-down-time}

$U_g$ and $D_g$ are the minimum up and down times in steps. Before each shutdown, the steps on in the rolling window of $U_g$ steps must cover the window; before each startup, the same holds for the steps off in a window of $D_g$ steps:

$$
\sum_{\tau=\max(0,\,t-U_g+1)}^{t} u_{g,\tau,s} + H^{up}_{g,t} \ge U_g \, y^{shutdown}_{g,t+1,s}
$$

$$
\sum_{\tau=\max(0,\,t-D_g+1)}^{t} \left(1 - u_{g,\tau,s}\right) + H^{down}_{g,t} \ge D_g \, y^{start}_{g,t+1,s}
$$

$H^{up}_{g,t}$ and $H^{down}_{g,t}$ count the window's steps before $t=0$ that the generator spent on (or off), from its initial state:

$$
H^{up}_{g,t} = u^0_g \min\big(T^0_g, \max(0, U_g - 1 - t)\big), \qquad
H^{down}_{g,t} = (1 - u^0_g) \min\big(T^0_g, \max(0, D_g - 1 - t)\big)
$$

A generator that has been on for less than its minimum up time cannot shut down at the first step, and one that has been off for less than its minimum down time cannot start:

$$
y^{shutdown}_{g,0,s} = 0 \;\text{ if } u^0_g = 1 \text{ and } T^0_g < U_g, \qquad
y^{start}_{g,0,s} = 0 \;\text{ if } u^0_g = 0 \text{ and } T^0_g < D_g
$$

Without `time_in_state`, $T^0_g$ is taken as longer than any window.

#### Initial and final state {#math-initial-final-state}

The initial state enters the constraints above through $p^0_g$, $u^0_g$ and $T^0_g$. A final state fixes the output at the last step:

$$
p_{g,T,s} = p^{end}_g
$$

#### Available capacity {#math-available-capacity}

$$
p_{g,t,s} \le A_{g,t,s}
$$

Only for generators with an `AvailableCapacityProfile` in scenario $s$.

### Objective contribution

The generation cost is subtracted from the profit $\Pi_s$:

$$
- \sum_{t,g} \left( c_g \, \Delta t \, p_{g,t,s} + C^{start}_g \, y^{start}_{g,t,s} + C^{shutdown}_g \, y^{shutdown}_{g,t,s} \right)
$$

The variable cost is per MWh, so the power is multiplied by the timestep length $\Delta t$. Startup and shutdown costs are per event.

### Power balance contribution

Supply side: $+\sum_g p_{g,t,s}$. See [Power balance](../concepts/power_balance.md).

## Next steps

Next, see how [FixedLoad](fixed_load.md) defines the demand your system must serve, or jump to [Battery](battery.md) to add storage.
