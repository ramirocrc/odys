---
icon: fontawesome/solid/plug
---

# FixedLoad

A `FixedLoad` represents inelastic demand that must be met exactly, like the factory of the [running example](../index.md#the-running-example). The optimizer cannot adjust it; it must dispatch generators, batteries, and markets to match.

Need demand the optimizer can shift up or down? See [FlexibleLoad](flexible_load.md).

## Basic usage

```python
from odys import FixedLoad

factory = FixedLoad(name="factory")
```

The actual demand values are specified later in the `Scenario` as a `LoadProfile`. We separate the load definition from its time series because the same load can appear in multiple scenarios with different profiles.

## Fields

| Field  | Type  | Required | Default | Description                    |
| ------ | ----- | -------- | ------- | ------------------------------ |
| `name` | `str` | Yes      | -       | Unique identifier for the load |

## Profiles

Every fixed load needs a `LoadProfile` in every scenario. It holds the demand at each timestep:

```python
from odys import LoadProfile, Scenario

scenario = Scenario(
    profiles=(LoadProfile(load=factory, values=[60, 90, 40, 70]),),
)
```

For multiple fixed loads, add one `LoadProfile` per load:

```python
offices = FixedLoad(name="offices")

scenario = Scenario(
    profiles=(
        LoadProfile(load=factory, values=[60, 90, 40, 70]),
        LoadProfile(load=offices, values=[5, 8, 8, 4]),
    ),
)
```

## Results

Fixed loads have no decision variables, so they have no results container. Their demand is exactly the `LoadProfile` you provided.

See the [Basic Dispatch example](../../examples/basic_dispatch.md) for a fixed load served by solar and a CCGT.

## Mathematical formulation

See [Mathematical notation](../mathematical_notation.md) for every symbol.

### Variables

None. The demand $d^{\text{fixed}}_{l,t,s}$ is a parameter taken from the `LoadProfile`.

### Constraints

None.

### Objective contribution

None. The cost of serving the load comes from the generators and markets that supply it.

### Power balance contribution

Demand side: $\sum_l d^{\text{fixed}}_{l,t,s}$. See [Power balance](../concepts/power_balance.md).

## Next steps

Next, let's give the optimizer demand it can shift: see [FlexibleLoad](flexible_load.md).
