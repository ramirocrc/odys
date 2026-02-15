# Load

A `Load` represents a demand that the energy system needs to satisfy. Loads come in two flavors: **fixed** and **flexible**.

## Basic usage

The simplest case is a fixed load -- the system must produce exactly this much power at each timestep:

```python
from odys.energy_system_models.assets.load import Load

load = Load(name="demand")
```

That's it. The actual demand values are specified later in the `Scenario` via `load_profiles`.

## Fields

| Field                       | Type       | Required | Default   | Description                                                     |
| --------------------------- | ---------- | -------- | --------- | --------------------------------------------------------------- |
| `name`                      | `str`      | Yes      | -         | Unique identifier for the load                                  |
| `type`                      | `LoadType` | No       | `"fixed"` | Either `"fixed"` or `"flexible"`                                |
| `variable_cost_to_increase` | `float`    | No       | `None`    | Cost per MWh for increasing load above baseline (flexible only) |
| `variable_cost_to_decrease` | `float`    | No       | `None`    | Cost per MWh for decreasing load below baseline (flexible only) |

## Fixed loads

A fixed load must be met exactly. The optimizer can't adjust it -- it has to dispatch generators and batteries to match.

```python
load = Load(name="factory_demand")
```

Then in your scenario:

```python
from odys.energy_system_models.scenarios import Scenario

scenario = Scenario(
    load_profiles={"factory_demand": [100, 120, 80, 90]},
)
```

The key in `load_profiles` must match the load's `name`.

## Flexible loads

A flexible load gives the optimizer some room to adjust demand up or down, but at a cost:

```python
from odys.energy_system_models.assets.load import Load, LoadType

flexible_load = Load(
    name="adjustable_demand",
    type=LoadType.Flexible,
    variable_cost_to_increase=30.0,
    variable_cost_to_decrease=20.0,
)
```

!!! warning

    For flexible loads, both `variable_cost_to_increase` and `variable_cost_to_decrease` are required. Pydantic will raise a validation error if you set the type to `"flexible"` without providing both costs.

## Load profiles

The actual demand timeseries is always provided through a `Scenario`, not on the `Load` object itself. This keeps the asset definition clean and lets you reuse the same load across different scenarios:

```python
from odys.energy_system_models.scenarios import Scenario

scenario = Scenario(
    load_profiles={
        "demand": [60, 90, 40, 70],
    },
)
```

For multiple loads, just add more entries:

```python
scenario = Scenario(
    load_profiles={
        "factory": [100, 120, 80, 90],
        "office": [20, 25, 15, 20],
    },
)
```
