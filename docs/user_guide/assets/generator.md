---
icon: fontawesome/solid/bolt
---

# Generator

A `Generator` represents any power source in your energy system: gas turbines, diesel generators, or wind and solar farms whose output is capped by the weather.

The optimizer decides how much power each generator produces at every timestep, and whether it is on or off, to maximize profit while meeting demand.

## Basic usage

Let's create the CCGT of the [running example](../index.md#the-running-example).

```python
from odys import Generator

ccgt = Generator(
    name="ccgt",
    nominal_power=100.0,
    variable_cost=50.0,
)
```

That's really all you need. The optimizer decides how much the CCGT produces at each timestep, weighing its 50 $/MWh cost against the other ways of meeting demand.

## Fields

| Field           | Type                | Required | Default | Description                                                        |
| --------------- | ------------------- | -------- | ------- | ------------------------------------------------------------------ |
| `name`          | `str`               | Yes      | -       | Unique identifier for the generator                                |
| `nominal_power` | `float`             | Yes      | -       | Maximum power output (MW)                                          |
| `variable_cost` | `float`             | Yes      | -       | Cost per unit of energy produced (currency/MWh)                    |
| `min_power`     | `float`             | No       | `0.0`   | Minimum power output when the generator is on (MW)                 |
| `ramp_up`       | `float \| None`     | No       | `None`  | Maximum increase in output from one timestep to the next (MW/step) |
| `ramp_down`     | `float \| None`     | No       | `None`  | Maximum decrease in output from one timestep to the next (MW/step) |
| `min_up_time`   | `timedelta \| None` | No       | `None`  | Minimum time the generator stays on once started                   |
| `min_down_time` | `timedelta \| None` | No       | `None`  | Minimum time the generator stays off once stopped                  |
| `startup_cost`  | `float`             | No       | `0.0`   | Cost of each startup (currency)                                    |
| `shutdown_cost` | `float`             | No       | `0.0`   | Cost of each shutdown (currency)                                   |

## Minimum power

When a generator is on, it must produce at least `min_power`. When it is off, it produces nothing. This models thermal plants that cannot run stably below a technical minimum.

```python
ccgt = Generator(
    name="ccgt",
    nominal_power=100.0,
    variable_cost=50.0,
    min_power=30.0,  # either off, or between 30 and 100 MW
)
```

See the [formulation](#math-power-limits).

## Ramp limits

If your generator can't change output instantly, set ramp limits. Real thermal plants can't jump from zero to full power in a single step; they need time to ramp up.

```python
ccgt = Generator(
    name="ccgt",
    nominal_power=100.0,
    variable_cost=50.0,
    min_power=30.0,
    ramp_up=40.0,  # can increase by at most 40 MW per step
    ramp_down=40.0,  # can decrease by at most 40 MW per step
)
```

Ramp limits are **per timestep**, not per hour: with 15-minute steps, `ramp_up=40.0` allows 40 MW every 15 minutes. When `ramp_up` or `ramp_down` is `None` (the default), there's no ramp constraint, and the generator can jump from 0 to full power in a single step. Use this for fast-responding assets or when ramp limits don't matter for your study.

Ramp limits also apply at the first step, measured from the generator's [initial state](#initial-and-final-state), so a generator with ramp limits needs one.

Odys has no separate startup or shutdown ramp rate. A generator whose `ramp_up` is below its `min_power` can never start, at the first step or later, because going from 0 MW to `min_power` breaks the ramp limit. Likewise, a generator whose `ramp_down` is below its output cannot shut down in one step.

See the [formulation](#math-ramp-limits).

## Minimum up and down time

`min_up_time` keeps a generator on for at least that long once it starts. `min_down_time` keeps it off for at least that long once it stops.

```python
from datetime import timedelta

ccgt = Generator(
    name="ccgt",
    nominal_power=100.0,
    variable_cost=50.0,
    min_up_time=timedelta(hours=4),  # once on, stays on for at least 4 hours
    min_down_time=timedelta(hours=3),  # once off, stays off for at least 3 hours
)
```

Both must be a whole number of timesteps. With 15-minute steps, `timedelta(minutes=45)` works, but `timedelta(minutes=50)` raises an `OdysValidationError` when the `EnergySystem` is created.

Time spent on or off before the horizon counts too: a generator that has been on for 1 hour with a 3-hour `min_up_time` must stay on for 2 more hours. That time comes from its [initial state](#initial-and-final-state).

See the [formulation](#math-min-up-down-time).

## Startup and shutdown cost

Both startup and shutdown cost are included in the objective, once per event.

```python
ccgt = Generator(
    name="ccgt",
    nominal_power=100.0,
    variable_cost=50.0,
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
from odys import (
    AssetPortfolio,
    EnergySystem,
    FixedLoad,
    GeneratorFinalState,
    GeneratorInitialState,
    LoadProfile,
    Scenario,
)

ccgt = Generator(
    name="ccgt",
    nominal_power=100.0,
    variable_cost=50.0,
    min_power=30.0,
    ramp_up=40.0,
    min_up_time=timedelta(hours=4),
)
factory = FixedLoad(name="factory")

energy_system = EnergySystem(
    portfolio=AssetPortfolio([ccgt, factory]),
    scenarios=Scenario(profiles=(LoadProfile(load=factory, values=[60, 90, 40, 70]),)),
    timestep=timedelta(hours=1),
    number_of_steps=4,
    initial_conditions=(GeneratorInitialState(generator=ccgt, power=50.0, time_in_state=timedelta(hours=2)),),
    final_conditions=(GeneratorFinalState(generator=ccgt, power=70.0),),
)
```

Here the CCGT has been producing 50 MW for 2 hours. That means:

- it can ramp to at most 90 MW at the first step;
- it must stay on for 2 more hours to complete its 4-hour minimum up time;
- it pays no startup cost;
- it must end at 70 MW.

A generator's state is its output: 0 MW means off, and any other output means on. A `GeneratorInitialState` is **required** when the generator's results depend on its starting state, which is the case when it has `ramp_up`, `ramp_down`, `min_up_time`, `min_down_time`, `startup_cost` or `shutdown_cost` set. Odys never guesses the starting state; a generator without these parameters needs no initial state and starts off.

The final output must fit the generator's available capacity at the last step in every scenario. An exact final output combined with ramp limits can make the problem infeasible, so give the generator enough steps to reach it.

See [Initial and final conditions](../concepts/initial_and_final_conditions.md#generators) for every field, including when `time_in_state` is required, and the [formulation](#math-initial-final-state).

## Profiles

In a `Scenario`, you can limit a generator's available capacity per timestep with an `AvailableCapacityProfile`. This is how you model weather-dependent output, like the wind farm of the running example, or planned maintenance:

```python
from odys import AvailableCapacityProfile

wind = Generator(name="wind", nominal_power=80.0, variable_cost=0.0)

scenario = Scenario(
    profiles=(
        AvailableCapacityProfile(generator=wind, values=[40, 10, 60, 30]),
        LoadProfile(load=factory, values=[60, 90, 40, 70]),
    ),
)
```

The profile references the generator object, and each value must lie between 0 and its `nominal_power`; otherwise building the profile raises an `OdysValidationError`. A generator without an `AvailableCapacityProfile` can produce up to its `nominal_power`.

See the [formulation](#math-available-capacity).

## Results

Let's solve the system with the CCGT's initial and final state from above and read its results through `result.generators`:

```python
result = energy_system.optimize()
print(result.generators.to_dataframe())
```

```text
                power  status  startup  shutdown
time generator
0    ccgt        60.0     1.0      0.0       0.0
1    ccgt        90.0     1.0      0.0       0.0
2    ccgt        40.0     1.0      0.0       0.0
3    ccgt        70.0     1.0      0.0       0.0
```

Notice there is no startup at step 0: the CCGT was already on, so it pays no startup cost.

The attributes are `power` (MW), `status` (1 when on), `startup` and `shutdown` (1 at the step the generator starts or stops). Each of these is a `pandas.Series` indexed by generator and time (and scenario, when there is more than one).

See the [Basic Dispatch example](../../examples/basic_dispatch.md) for a full day of solar and CCGT dispatch.

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

Next, see how [FixedLoad](fixed_load.md) defines the demand your system must serve.
