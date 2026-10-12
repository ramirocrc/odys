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
| `min_up_time`   | `int`           | No       | `1`     | Minimum number of timesteps the generator must stay on  |
| `min_down_time` | `int`           | No       | `1`     | Minimum number of timesteps the generator must stay off |
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

See the [formulation](#math-ramp-limits).

## Minimum up and down time

`min_up_time` keeps a generator on for at least that many timesteps once it starts. `min_down_time` keeps it off for at least that many timesteps once it stops.

```python
gen = Generator(
    name="coal_plant",
    nominal_power=500.0,
    variable_cost=25.0,
    min_up_time=4,  # once on, stays on for at least 4 steps
    min_down_time=3,  # once off, stays off for at least 3 steps
)
```

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

See the [formulation](#math-startup-shutdown).

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

For $t \ge 1$:

$$
p_{g,t,s} - p_{g,t-1,s} \le R^{up}_g, \qquad p_{g,t-1,s} - p_{g,t,s} \le R^{down}_g
$$

When a ramp limit is not set, it defaults to $P^{\max}_g$, which never binds.

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

Before the horizon, every generator is off: $u_{g,-1,s} = 0$.

#### Minimum up and down time {#math-min-up-down-time}

$$
\sum_{\tau=t-U_g+1}^{t} u_{g,\tau,s} \ge U_g \, y^{shutdown}_{g,t+1,s}
$$

$$
\sum_{\tau=t-D_g+1}^{t} \left(1 - u_{g,\tau,s}\right) \ge D_g \, y^{start}_{g,t+1,s}
$$

A generator may only shut down at $t+1$ if it has been on for the last $U_g$ steps, and only start at $t+1$ if it has been off for the last $D_g$ steps. Both apply for windows that fit in the horizon.

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
