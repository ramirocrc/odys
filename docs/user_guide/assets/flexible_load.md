---
icon: fontawesome/solid/sliders
---

# FlexibleLoad

A `FlexibleLoad` models demand the optimizer may set anywhere within a range: a cold store that can run harder when power is cheap, a process that can slow down when it's expensive, or a site in a demand response programme.

Each scenario gives the range at every step, and the optimizer decides where in it the load runs, weighing what the consumption is worth against what the power costs.

## Basic usage

Let's add a flexible process to the site: each MWh it consumes is worth 60 $/MWh to the site.

```python
from odys import FlexibleLoad

process = FlexibleLoad(name="process", value_of_consumption=60.0)
```

## Fields

| Field                  | Type            | Required | Default | Description                                                 |
| ---------------------- | --------------- | -------- | ------- | ----------------------------------------------------------- |
| `name`                 | `str`           | Yes      | -       | Unique name of the load                                     |
| `value_of_consumption` | `float`         | Yes      | -       | Value of each MWh consumed, at least 0 (currency/MWh)       |
| `min_load`             | `float \| None` | No       | `None`  | Least the load can consume while running, at least 0 (MW)   |
| `max_load`             | `float \| None` | No       | `None`  | Most the load can consume while running, above 0 (MW)       |
| `ramp_up`              | `float \| None` | No       | `None`  | Fastest the consumption can rise, at least 0 (MW per hour)  |
| `ramp_down`            | `float \| None` | No       | `None`  | Fastest the consumption can fall, at least 0 (MW per hour)  |
| `commitment`           | `Commitment \| None` | No  | `None`  | How the load switches on and off; `None` keeps it always on |

`min_load` can't be above `max_load`.

## Value of consumption

`value_of_consumption` is what each MWh the load consumes is worth to you. It's what the optimizer weighs against the cost of the power the load would draw:

- When it's above what one more MWh costs, from your generators or the market, the optimizer runs the load higher.
- When it's below, the optimizer runs the load lower, and uses or sells that power elsewhere.

The process above is worth 60 $/MWh. When the CCGT at 50 $/MWh is the most expensive supply running, the process runs as high as it can. With `value_of_consumption=0.0`, consuming is worth nothing, so the optimizer keeps the load at its lower bound whenever power costs anything at all.

The cost of the power never appears on the load itself: it shows up in the generators and markets that supply it. See [the objective contribution](../../formulation/flexible_loads.md#objective-contribution).

## Profiles

Every flexible load needs a `FlexibleLoadProfile` in every scenario. It gives the range the load can run in at each step: `lower_bound` is the least it consumes, and `upper_bound` the most, both in MW. Say the process can run anywhere from 20 to 50 MW:

```python
from odys import FlexibleLoadProfile, Scenario

scenario = Scenario(
    profiles=(FlexibleLoadProfile(load=process, lower_bound=[20, 20, 20, 20], upper_bound=[50, 50, 50, 50]),),
)
```

The range can change from step to step, and from one scenario to the next: a process that has to keep a furnace warm overnight, or an order that may or may not come in.

Each step stands on its own: energy not used now isn't used later, and without [ramp limits](#ramp-limits) the load can jump across its whole range from one step to the next. See [FL-1](../../formulation/flexible_loads.md#fl-1).

Building a `FlexibleLoadProfile` raises an `OdysValidationError` unless, at every step, the lower bound is at least 0 and at most the upper bound, and both bounds have the same number of values.

### Physical limits

`min_load` and `max_load` are the load's own limits, whatever the scenario: a hard minimum to keep it running, or what its connection allows. Every bound of every scenario has to fit inside them:

```python
from odys import OdysValidationError

compressor = FlexibleLoad(name="compressor", max_load=40.0, value_of_consumption=60.0)

try:
    FlexibleLoadProfile(load=compressor, lower_bound=[20, 20], upper_bound=[40, 45])
except OdysValidationError as error:
    print(error)
```

```text
Flexible load 'compressor' has an upper bound (45.0) above max_load (40.0) at time index 1.
```

## Results

Let's add the process to the CCGT, the wind farm and the factory, and read its results through `result.flexible_loads`:

```python
from datetime import timedelta

from odys import AssetPortfolio, AvailableCapacityProfile, EnergySystem, FixedLoad, Generator, LoadProfile

ccgt = Generator(name="ccgt", nominal_power=100.0, variable_cost=50.0)
wind = Generator(name="wind", nominal_power=80.0, variable_cost=0.0)
factory = FixedLoad(name="factory")

energy_system = EnergySystem(
    portfolio=AssetPortfolio([ccgt, wind, factory, process]),
    scenarios=Scenario(
        profiles=(
            LoadProfile(load=factory, values=[60, 90, 40, 70]),
            FlexibleLoadProfile(load=process, lower_bound=[20, 20, 20, 20], upper_bound=[50, 50, 50, 50]),
            AvailableCapacityProfile(generator=wind, values=[40, 10, 60, 30]),
        ),
    ),
    timestep=timedelta(hours=1),
    number_of_steps=4,
)

result = energy_system.optimize()
print(result.flexible_loads.to_dataframe())
```

```text
                    consumption  status  startup  shutdown
time flexible_load
0    process               50.0     1.0      0.0       0.0
1    process               20.0     1.0      0.0       0.0
2    process               50.0     1.0      0.0       0.0
3    process               50.0     1.0      0.0       0.0
```

`result.flexible_loads` has four series, each a `pandas.Series` indexed by load and time, and by scenario when there's more than one:

- `consumption`: what the load consumes, in MW;
- `status`: 1 while the load runs, 0 while it's off. A load without a [commitment](#switching-on-and-off) is always on;
- `startup` and `shutdown`: 1 at the step the load starts or stops.

Every MWh of the process is worth 60 $/MWh and the most expensive supply, the CCGT, costs 50 $/MWh, so the optimizer runs the process at its upper bound whenever it can. At step 1 the factory needs 90 MW and only 110 MW of supply is available, so the process drops to its lower bound instead.

The [Industrial Demand Response](../../examples/demand_response.md) example follows a process through a full day of market prices.

## Ramp limits

A big process can't change its draw in an instant: a kiln heats up and cools down slowly. `ramp_up` and `ramp_down` say how fast its consumption can change, in MW per hour:

```python
kiln = FlexibleLoad(name="kiln", value_of_consumption=40.0, ramp_up=20.0)
```

With hourly steps, the kiln's consumption rises by at most 20 MW from one step to the next; with 15-minute steps, by 5 MW. Without `ramp_down`, it can fall as fast as it likes. At the first step, the limit counts from where the load was just before the run, its [initial state](#initial-state). See [FL-3](../../formulation/flexible_loads.md#fl-3) and [FL-4](../../formulation/flexible_loads.md#fl-4).

## Switching on and off

Some processes can stop altogether, but can't run below a minimum stable load: a kiln runs between 30 and 70 MW, or not at all. Give such a load a `Commitment`, the same one a [generator](generator.md#minimum-up-and-down-time) takes:

```python
from datetime import timedelta

from odys import Commitment

kiln = FlexibleLoad(
    name="kiln",
    value_of_consumption=40.0,
    ramp_up=20.0,
    commitment=Commitment(min_up_time=timedelta(hours=2), startup_cost=200.0),
)
```

Now at every step the kiln is either off, at 0 MW, or running within its `FlexibleLoadProfile` range, so the lower bound becomes its minimum stable load. Once started, it runs for at least 2 hours, and each start costs 200. A `Commitment` can also hold a `min_down_time` and a `shutdown_cost`. Without a commitment, a load is always on and never consumes less than its lower bound.

Ramps only limit the change between two steps the load runs: a start can land anywhere in the range, and a stop drops straight to 0. See [FL-2](../../formulation/flexible_loads.md#fl-2).

## Initial state

A ramp limit, a minimum up or down time and a start-up or shut-down cost all depend on where the load was before the run. So as soon as a load has one, odys asks for a `FlexibleLoadInitialState`: its `load`, its `power` just before the first step, and, for a load with a commitment, its `time_in_state`, how long it has been running, or off when `power` is 0. `time_in_state` is needed when the matching minimum time is set, and it has to be a whole number of steps. `power` is 0, for a load that can switch off, or within `min_load` and `max_load`.

Say the kiln has been running at 30 MW for an hour, and only the wind farm is cheaper than what the kiln's output is worth, with a lull in the middle of the day:

```python
from odys import FlexibleLoadInitialState

ccgt = Generator(name="ccgt", nominal_power=100.0, variable_cost=60.0)

energy_system = EnergySystem(
    portfolio=AssetPortfolio([ccgt, wind, kiln]),
    scenarios=Scenario(
        profiles=(
            FlexibleLoadProfile(load=kiln, lower_bound=[30] * 6, upper_bound=[70] * 6),
            AvailableCapacityProfile(generator=wind, values=[70, 70, 10, 10, 80, 80]),
        ),
    ),
    timestep=timedelta(hours=1),
    number_of_steps=6,
    initial_conditions=(FlexibleLoadInitialState(load=kiln, power=30.0, time_in_state=timedelta(hours=1)),),
)

result = energy_system.optimize()
print(result.flexible_loads.to_dataframe())
```

```text
                    consumption  status  startup  shutdown
time flexible_load
0    kiln                  50.0     1.0      0.0       0.0
1    kiln                  70.0     1.0      0.0       0.0
2    kiln                   0.0     0.0      0.0       1.0
3    kiln                   0.0     0.0      0.0       0.0
4    kiln                  70.0     1.0      1.0       0.0
5    kiln                  70.0     1.0      0.0       0.0
```

The kiln climbs from 30 MW as fast as its ramp allows, 20 MW an hour, to run on the free wind. During the lull, staying on at its 30 MW floor would mean burning CCGT power worth less than it costs, and climbing back at 20 MW an hour once the wind returns. Stopping is better: at step 4 it restarts straight at 70 MW, for one start-up of 200.

## How it's modelled

A flexible load has one decision per step: how much it consumes, and, with a commitment, whether it runs. [FL-1](../../formulation/flexible_loads.md#fl-1) keeps it between the lower and the upper bound while it runs, [FL-3](../../formulation/flexible_loads.md#fl-3) and [FL-4](../../formulation/flexible_loads.md#fl-4) limit its ramps, and all of the consumption is valued at `value_of_consumption` in the objective, less the start-up and shut-down costs. The rule, why it's written that way, and its limitations are on the [Flexible loads](../../formulation/flexible_loads.md) formulation page.

## Next steps

A flexible load changes how much you consume, not when. To move energy from one step to another, store it: see [Battery](battery.md).
