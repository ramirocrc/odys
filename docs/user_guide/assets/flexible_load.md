---
icon: fontawesome/solid/sliders
---

# FlexibleLoad

A `FlexibleLoad` models demand the optimizer may move up or down within limits: a cold store that can run harder when power is cheap, a process that can slow down when it's expensive, or a site in a demand response programme.

It starts from a base profile, and at every step the optimizer decides how far to raise or lower it, weighing what the consumption is worth against what the power costs.

## Basic usage

Let's add a flexible process to the site: it normally draws 30 MW, can run 20 MW higher or 10 MW lower, and each MWh it consumes is worth 60 $/MWh to the site.

```python
from odys import FlexibleLoad

process = FlexibleLoad(
    name="process",
    max_increase=20.0,
    max_decrease=10.0,
    value_of_consumption=60.0,
)
```

## Fields

| Field                  | Type            | Required | Default | Description                                                     |
| ---------------------- | --------------- | -------- | ------- | --------------------------------------------------------------- |
| `name`                 | `str`           | Yes      | -       | Unique name of the load                                         |
| `value_of_consumption` | `float`         | Yes      | -       | Value of each MWh consumed, at least 0 (currency/MWh)           |
| `max_increase`         | `float \| None` | No*      | `None`  | Most the load can rise above its base, above 0 (MW)             |
| `max_decrease`         | `float \| None` | No*      | `None`  | Most the load can fall below its base, above 0 (MW)             |
| `min_load`             | `float \| None` | No*      | `None`  | Lowest the load can go, at least 0 (MW). Overrides `max_decrease` |
| `max_load`             | `float \| None` | No*      | `None`  | Highest the load can go, above 0 (MW). Overrides `max_increase`  |

\* Each side needs a limit: `max_decrease` or `min_load` for the floor, and `max_increase` or `max_load` for the ceiling. `min_load` can't be above `max_load`.

## Value of consumption

`value_of_consumption` is what each MWh the load consumes is worth to you. It's what the optimizer weighs against the cost of the power the load would draw:

- When it's above what one more MWh costs, from your generators or the market, the optimizer raises the load.
- When it's below, the optimizer lowers the load, and uses or sells that power elsewhere.

The process above is worth 60 $/MWh. When the CCGT at 50 $/MWh is the most expensive supply running, the process runs as high as it can. With `value_of_consumption=0.0`, cutting the load costs nothing, so the optimizer cuts it whenever power costs anything at all.

The cost of the extra power never appears on the load itself: it shows up in the generators and markets that supply it. See [the objective contribution](../../formulation/flexible_loads.md#objective-contribution).

## How far demand can move

Each side of the range is limited in one of two ways: **relative** to the base profile, or **absolute**. The process above uses relative limits: with a base of 30 MW, `max_increase=20.0` and `max_decrease=10.0` let it run anywhere from 20 to 50 MW.

Use absolute limits when the process has hard limits that don't depend on the base, for example a process that can run anywhere from 15 to 50 MW:

```python
bounded_process = FlexibleLoad(
    name="process",
    min_load=15.0,
    max_load=50.0,
    value_of_consumption=60.0,
)
```

You can mix them, one kind per side. When you set both on one side, the absolute limit is used and the relative one is ignored, even when it's the tighter one: with `max_decrease=10.0` and `min_load=15.0`, the floor is 15 MW, not 20 MW.

Each step stands on its own: energy cut now isn't made up later, and the load can jump across its whole range from one step to the next. See [FL-1](../../formulation/flexible_loads.md#fl-1).

## Profiles

Every flexible load needs a `LoadProfile` in every scenario. This is the **base profile**: the demand the optimizer starts from before making adjustments.

```python
from odys import LoadProfile, Scenario

scenario = Scenario(
    profiles=(LoadProfile(load=process, values=[30, 30, 30, 30]),),
)
```

Every base value has to fit the load's limits, or building the `LoadProfile` raises an `OdysValidationError`:

- at least `min_load` and at most `max_load`, for whichever of them is set;
- at least `max_decrease` when `min_load` is not set, so the adjusted load can never go negative.

## Results

Let's add the process to the CCGT, the wind farm and the factory, and read its results through `result.flexible_loads`:

```python
from datetime import timedelta

from odys import AssetPortfolio, AvailableCapacityProfile, EnergySystem, FixedLoad, Generator

ccgt = Generator(name="ccgt", nominal_power=100.0, variable_cost=50.0)
wind = Generator(name="wind", nominal_power=80.0, variable_cost=0.0)
factory = FixedLoad(name="factory")

energy_system = EnergySystem(
    portfolio=AssetPortfolio([ccgt, wind, factory, process]),
    scenarios=Scenario(
        profiles=(
            LoadProfile(load=factory, values=[60, 90, 40, 70]),
            LoadProfile(load=process, values=[30, 30, 30, 30]),
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
                    load_adjustment  actual_load
time flexible_load
0    process                   20.0         50.0
1    process                  -10.0         20.0
2    process                   20.0         50.0
3    process                   20.0         50.0
```

`result.flexible_loads` has two series, each a `pandas.Series` indexed by load and time, and by scenario when there's more than one:

- `load_adjustment`: the change from the base profile, in MW, positive when the load rises.
- `actual_load`: what the load consumes, the base plus the adjustment, in MW.

Every MWh of the process is worth 60 $/MWh and the most expensive supply, the CCGT, costs 50 $/MWh, so the optimizer runs the process 20 MW above its base whenever it can. At step 1 the factory needs 90 MW and only 110 MW of supply is available, so the process drops 10 MW below its base instead.

See the [Flexible Load Market example](../../examples/flexible_load_market.md) for a full day of demand response against market prices.

## How it's modelled

A flexible load has one decision per step: how far to move away from its base. [FL-1](../../formulation/flexible_loads.md#fl-1) keeps the adjusted load between its floor and its ceiling, and the adjustment is valued at `value_of_consumption` in the objective. The rule, why it's written that way, and its limitations are on the [Flexible loads](../../formulation/flexible_loads.md) formulation page.

## Next steps

A flexible load changes how much you consume, not when. To move energy from one step to another, store it: see [Battery](battery.md).
