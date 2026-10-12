---
icon: fontawesome/solid/plug
---

# FixedLoad

A `FixedLoad` represents inelastic demand that must be met exactly. The optimizer cannot adjust it; it must dispatch generators, batteries, and markets to match.

Need demand the optimizer can shift up or down? See [FlexibleLoad](flexible_load.md).

## Basic usage

```python
from odys import FixedLoad

load = FixedLoad(name="factory_demand")
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
    profiles=(LoadProfile(load=load, values=[100, 120, 80, 90]),),
)
```

For multiple fixed loads, add one `LoadProfile` per load:

```python
factory = FixedLoad(name="factory")
office = FixedLoad(name="office")

scenario = Scenario(
    profiles=(
        LoadProfile(load=factory, values=[100, 120, 80, 90]),
        LoadProfile(load=office, values=[20, 25, 15, 20]),
    ),
)
```

## Results

Fixed loads have no decision variables, so they have no results container. Their demand is exactly the `LoadProfile` you provided.

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

Want demand that responds to prices? See [FlexibleLoad](flexible_load.md).
