---
icon: fontawesome/solid/plug
---

# FixedLoad

A `FixedLoad` models demand that has to be served exactly as given: a building, a process that can't move, a site's base consumption, like the factory of the [running example](../index.md#the-running-example). The optimizer can't change it. It decides how your generators, batteries and markets cover it.

For demand the optimizer may move up or down, use a [FlexibleLoad](flexible_load.md) instead.

## Basic usage

```python
from odys import FixedLoad

factory = FixedLoad(name="factory")
```

A fixed load is just a name. Its demand lives in each `Scenario`, as a `LoadProfile` (see [Profiles](#profiles)), because the same factory can draw differently in different futures.

## Fields

| Field  | Type  | Required | Default | Description               |
| ------ | ----- | -------- | ------- | ------------------------- |
| `name` | `str` | Yes      | -       | Unique name of the load   |

## Profiles

Every fixed load needs a `LoadProfile` in every scenario, with its demand in MW at each step:

```python
from odys import LoadProfile, Scenario

scenario = Scenario(
    profiles=(LoadProfile(load=factory, values=[60, 90, 40, 70]),),
)
```

With several fixed loads, give each one its own profile:

```python
offices = FixedLoad(name="offices")

scenario = Scenario(
    profiles=(
        LoadProfile(load=factory, values=[60, 90, 40, 70]),
        LoadProfile(load=offices, values=[5, 8, 8, 4]),
    ),
)
```

The profile needs one value per step of the run. Every MW of it has to be served: there is no unserved energy, so if your assets and markets can't cover the demand at some step, the problem is infeasible. odys catches the obvious cases before solving, when even all your supply together falls short, and raises an `OdysValidationError`. See [PB-1](../../formulation/power_balance.md#pb-1).

## Results

A fixed load has no decisions, so it has no results container: its demand is exactly the `LoadProfile` you gave. What the optimizer decided shows up in the assets and markets that serve it. The [Basic Dispatch example](../../examples/basic_dispatch.md) serves a fixed load with solar and a CCGT.

## How it's modelled

A fixed load adds its demand to the [power balance](../../formulation/power_balance.md#fixed-loads), and nothing else: no variables, no constraints of its own, and no term in the objective. Serving it costs whatever the energy that covers it costs.

## Next steps

Some demand can bend when prices do. Next, see how a [FlexibleLoad](flexible_load.md) lets the optimizer move it.
