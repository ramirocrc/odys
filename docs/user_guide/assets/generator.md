---
icon: fontawesome/solid/bolt
---

# Generator

A `Generator` models a gas turbine, a diesel engine, or a wind or solar farm whose output depends on the weather. You give its rating and its cost per MWh, and the optimizer decides how much it produces at every step, and whether it's on at all.

That's enough for a wind farm. A thermal plant usually needs a few more fields: a minimum output, ramp limits, minimum up and down times, and start-up and shut-down costs. Each one is optional, and this page goes through them one by one.

## Basic usage

Let's create the CCGT of the site from [Your first model](../model/first_model.md): a 100 MW gas plant whose fuel costs 50 $/MWh.

```python
from odys import Generator

ccgt = Generator(
    name="ccgt",
    nominal_power=100.0,
    variable_cost=50.0,
)
```

That's all a generator needs. The optimizer runs the CCGT whenever its 50 $/MWh beats the other ways of serving demand, anywhere between 0 and 100 MW, and switches it off when it doesn't.

## Fields

| Field           | Type                | Required | Default | Description                                                   |
| --------------- | ------------------- | -------- | ------- | ------------------------------------------------------------- |
| `name`          | `str`               | Yes      | -       | Unique name of the generator                                  |
| `nominal_power` | `float`             | Yes      | -       | Rated output, above 0 (MW)                                    |
| `variable_cost` | `float`             | Yes      | -       | Cost of each MWh produced, at least 0 (currency/MWh)          |
| `min_power`     | `float`             | No       | `0.0`   | Lowest output while on (MW)                                   |
| `ramp_up`       | `float \| None`     | No       | `None`  | Fastest the output can rise (MW per hour)                     |
| `ramp_down`     | `float \| None`     | No       | `None`  | Fastest the output can fall (MW per hour)                     |
| `commitment`    | `Commitment`        | No       | `Commitment()` | How it switches on and off: minimum up and down times, start-up and shut-down costs |

A `Commitment` holds the rules for switching on and off:

| Field           | Type                | Required | Default | Description                                         |
| --------------- | ------------------- | -------- | ------- | --------------------------------------------------- |
| `min_up_time`   | `timedelta \| None` | No       | `None`  | Shortest time the generator stays on once started   |
| `min_down_time` | `timedelta \| None` | No       | `None`  | Shortest time the generator stays off once stopped  |
| `startup_cost`  | `float`             | No       | `0.0`   | Cost of each start-up, at least 0 (currency)        |
| `shutdown_cost` | `float`             | No       | `0.0`   | Cost of each shut-down, at least 0 (currency)       |

The default, `Commitment()`, lets the generator switch on and off freely, at no cost.

## Minimum power

Many plants can't run stably at just any output. A gas turbine at 5 % load is inefficient at best, so it has a technical minimum. Set `min_power`, and the generator is either off or at least at that output:

```python
ccgt = Generator(
    name="ccgt",
    nominal_power=100.0,
    variable_cost=50.0,
    min_power=30.0,  # either off, or between 30 and 100 MW
)
```

Now the CCGT can't follow a 20 MW demand on its own. The optimizer has to choose: run at 30 MW and do something with the extra 10 MW, or switch off and find the 20 MW elsewhere. That choice is what makes generators an on/off decision. See [G-3](../../formulation/generators.md#g-3).

## Ramp limits

A big plant also can't jump from low to full output in an instant. Ramp limits say how fast its output can change:

```python
ccgt = Generator(
    name="ccgt",
    nominal_power=100.0,
    variable_cost=50.0,
    min_power=30.0,
    ramp_up=40.0,  # up by at most 40 MW per hour
    ramp_down=40.0,  # down by at most 40 MW per hour
)
```

With hourly steps, going from 30 to 100 MW takes two steps. The limits are **per hour**, whatever the step length: with 15-minute steps, `ramp_up=40.0` allows 10 MW per step. Leave them at `None` for a unit that can follow any change, like a wind farm.

Ramps also count when the generator starts or stops, and at the first step, where they start from the generator's [initial state](#initial-and-final-state). So keep one step's worth of `ramp_up` at or above `min_power`, or the unit can't reach its minimum and never starts. See [G-7](../../formulation/generators.md#g-7).

## Minimum up and down time

Once started, a big plant has to stay on for a while, and once stopped, it needs time to cool down before it starts again. Both go in its `Commitment`:

```python
from datetime import timedelta

from odys import Commitment

ccgt = Generator(
    name="ccgt",
    nominal_power=100.0,
    variable_cost=50.0,
    commitment=Commitment(
        min_up_time=timedelta(hours=4),  # once on, on for at least 4 hours
        min_down_time=timedelta(hours=3),  # once off, off for at least 3 hours
    ),
)
```

The optimizer now thinks ahead: switching the CCGT on for one expensive hour means keeping it on for four. Both times must be a whole number of steps. With 15-minute steps, 45 minutes works, and 50 minutes raises an `OdysValidationError` when you create the `EnergySystem`.

Time spent before the run counts too: a CCGT that has been on for 1 hour, with a 3-hour `min_up_time`, stays on for the first 2 hours. That time comes from its [initial state](#initial-and-final-state). See [G-8](../../formulation/generators.md#g-8) and [G-9](../../formulation/generators.md#g-9).

## Startup and shutdown cost

Starting a thermal plant burns fuel and wears it out before it produces a single MWh. Put a price on each start-up and each shut-down in its `Commitment`, and the optimizer thinks twice before switching:

```python
ccgt = Generator(
    name="ccgt",
    nominal_power=100.0,
    variable_cost=50.0,
    commitment=Commitment(startup_cost=500.0, shutdown_cost=200.0),
)
```

Each cost is paid once per event, however long the step. With them, keeping the CCGT running through a cheap hour can beat stopping it and starting it again. A generator that is already on at the start of the run, from its [initial state](#initial-and-final-state), pays no start-up cost for running at the first step. See [G-5](../../formulation/generators.md#g-5) and [Objective](../../formulation/objective.md#profit-per-scenario).

## Initial and final state

Say you're optimizing tomorrow's dispatch, starting at midnight, and the CCGT is running tonight: by midnight, it will have been producing 50 MW for 2 hours. Tomorrow's plan has to pick up from there, so you pass that state as a `GeneratorInitialState`. If tomorrow also has to hand over to the day after, a `GeneratorFinalState` sets the output the CCGT ends with. Both go to the [EnergySystem](../model/first_model.md#initial-and-final-conditions). Here we plan tomorrow's first four hours:

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
    commitment=Commitment(min_up_time=timedelta(hours=4)),
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

Starting from 50 MW, with 2 hours already on, the CCGT:

- can ramp to at most 90 MW in the first hour;
- stays on for at least 2 more hours, to complete its 4-hour minimum up time;
- pays no start-up cost, because it's already on;
- ends the run at exactly 70 MW.

A generator is on whenever its output is above 0. odys asks for an initial state as soon as the start matters: when the generator has a ramp limit, a minimum up or down time, or a start-up or shut-down cost. Without any of these, it starts off. Pick a final output the generator can reach: combined with ramp limits, an exact final output can make the problem infeasible.

A `GeneratorInitialState` takes the `generator`, its `power` just before the first step, and `time_in_state`: how long it has been on, or off when `power` is 0. The `power` is either 0 or between `min_power` and `nominal_power`; anything else raises an `OdysValidationError`. `time_in_state` is needed when the matching minimum time is set: `min_up_time` for a unit that starts on, `min_down_time` for one that starts off. It has to be a whole number of steps. Leave it out otherwise, and the unit counts as having been in its state long enough. See [G-5](../../formulation/generators.md#g-5) and [G-8](../../formulation/generators.md#g-8).

A `GeneratorFinalState` takes the `generator` and the `power` it ends the run with, in the same range, and within its available capacity at the last step. See [G-10](../../formulation/generators.md#g-10).

## Profiles

The wind doesn't always blow. In a `Scenario`, an `AvailableCapacityProfile` caps a generator's output at every step. Use it for wind and solar, like a wind farm, or for planned maintenance:

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

The profile references the generator object, and each value lies between 0 and its `nominal_power`; anything else raises an `OdysValidationError`. A generator without a profile can always produce up to its `nominal_power`. Each scenario can have its own profile, which is how a windy and a calm tomorrow differ (see [Several scenarios](../uncertainty/scenarios.md)). See [G-4](../../formulation/generators.md#g-4).

## Results

Let's solve the system with the CCGT's initial and final state from above, and read its plan through `result.generators`:

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

The CCGT is the only supply, so it follows the factory's demand, within its ramp limits. Notice there's no start-up at step 0: it was already on.

`result.generators` has four series, each a `pandas.Series` indexed by generator and time, and by scenario when there's more than one:

- `power`: the output, in MW.
- `status`: 1 when the generator is on. A generator that's on always produces something, so `status` and `power > 0` agree ([G-2](../../formulation/generators.md#g-2)).
- `startup` and `shutdown`: 1 at the step where the generator starts or stops.

## How it's modelled

A generator has an output and an on/off status at every step, in every scenario. The status ties the output to its limits and counts every start-up and shut-down, which is what the minimum times and switching costs build on. Every rule, why it's written that way, and its limitations are on the [Generators](../../formulation/generators.md) formulation page, from [G-1](../../formulation/generators.md#g-1) to [G-10](../../formulation/generators.md#g-10).

## Next steps

A generator produces power, but for whom? Next, see how [FixedLoad](fixed_load.md) defines the demand your system has to serve.
