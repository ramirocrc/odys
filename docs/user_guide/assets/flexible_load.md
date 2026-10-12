---
icon: fontawesome/solid/sliders
---

# FlexibleLoad

A `FlexibleLoad` gives the optimizer room to adjust demand up or down within bounds. Use this for demand response programs, industrial processes that can shift load, or any consumption that has economic value but timing flexibility.

The optimizer starts from a base profile and decides, at every timestep, how much to raise or lower it.

## Basic usage

```python
from odys import FlexibleLoad

flexible_load = FlexibleLoad(
    name="industrial_process",
    max_increase=50.0,
    max_decrease=30.0,
    value_of_consumption=100.0,
)
```

## Fields

| Field                  | Type            | Required | Default | Description                                                                          |
| ---------------------- | --------------- | -------- | ------- | ------------------------------------------------------------------------------------ |
| `name`                 | `str`           | Yes      | -       | Unique identifier for the load                                                       |
| `value_of_consumption` | `float`         | Yes      | -       | Economic value of consuming electricity in currency per MWh (must be >= 0)           |
| `max_increase`         | `float \| None` | No*      | `None`  | Maximum MW the load can increase above the base profile (must be > 0)                |
| `max_decrease`         | `float \| None` | No*      | `None`  | Maximum MW the load can decrease below the base profile (must be > 0)                |
| `min_load`             | `float \| None` | No*      | `None`  | Absolute minimum consumption in MW (must be >= 0). Overrides `max_decrease` when set |
| `max_load`             | `float \| None` | No*      | `None`  | Absolute maximum consumption in MW (must be > 0). Overrides `max_increase` when set  |

\* Each side needs at least one bound: `max_decrease` or `min_load` for the lower side, `max_increase` or `max_load` for the upper side. If both are set on a side, the absolute bound wins. `min_load` must not exceed `max_load`.

## Value of consumption

The optimizer decides whether to increase or decrease load based on economics. Every MWh of extra consumption earns `value_of_consumption`, and every MWh of reduced consumption loses it.

The procurement cost of adjusting load is captured implicitly through the power balance: when the optimizer increases load, it must procure more energy from generators or markets (whose costs are already in the objective). When it decreases load, it frees up supply for other uses (e.g., selling to markets).

- When `value_of_consumption` exceeds the marginal supply cost, increasing load is profitable.
- When the marginal supply cost exceeds `value_of_consumption`, decreasing load saves money.

See the [formulation](#math-objective).

## Relative bounds

`max_increase` and `max_decrease` bound the adjustment relative to the base profile. With the load above and a base of 80 MW, consumption can move between 50 and 130 MW.

See the [formulation](#math-bounds).

## Absolute bounds

Use `min_load` and `max_load` when the process has hard physical limits that don't depend on the base profile, for example a compressor that can run between 20 and 100 MW:

```python
compressor = FlexibleLoad(
    name="compressor",
    min_load=20.0,
    max_load=100.0,
    value_of_consumption=40.0,
)
```

When set, an absolute bound replaces the relative bound on that side at every timestep.

See the [formulation](#math-bounds).

## Profiles

Every flexible load needs a `LoadProfile` in every scenario. This is the **base profile**: the demand the optimizer starts from before making adjustments.

```python
from odys import LoadProfile, Scenario

scenario = Scenario(
    profiles=(LoadProfile(load=flexible_load, values=[80, 80, 80, 80]),),
)
```

Every base value must lie within the load's bounds, otherwise building the `LoadProfile` raises an `OdysValidationError`:

- at least `min_load` and at most `max_load`, for whichever of them is set;
- at least `max_decrease` when `min_load` is not set, so the adjusted load can never go negative.

## Results

After optimization, access flexible load results through `result.flexible_loads`:

```python
result = energy_system.optimize()

result.flexible_loads.load_adjustment  # MW adjustment per timestep
result.flexible_loads.actual_load  # MW consumed (base + adjustment)
```

See the [Flexible Load Market example](../../examples/flexible_load_market.md) for a full worked scenario.

## Mathematical formulation

See [Mathematical notation](../mathematical_notation.md) for every symbol.

### Variables

| Symbol | Result attribute | Domain | Meaning |
| ------ | ---------------- | ------ | ------- |
| $\Delta d_{l,t,s}$ | `load_adjustment` | $\mathbb{R}$ | Adjustment of the base profile (positive = increase) |
| $d_{l,t,s} = d^{\text{base}}_{l,t,s} + \Delta d_{l,t,s}$ | `actual_load` | - | Actual consumption |

### Constraints

#### Bounds {#math-bounds}

Lower side, with `min_load` set or not:

$$
d^{\text{base}}_{l,t,s} + \Delta d_{l,t,s} \ge D^{\min}_l
\qquad \text{or} \qquad
\Delta d_{l,t,s} \ge -\Delta d^{\max-}_l
$$

Upper side, with `max_load` set or not:

$$
d^{\text{base}}_{l,t,s} + \Delta d_{l,t,s} \le D^{\max}_l
\qquad \text{or} \qquad
\Delta d_{l,t,s} \le \Delta d^{\max+}_l
$$

### Objective contribution {#math-objective}

The value of the adjusted consumption is added to the profit $\Pi_s$:

$$
+ \sum_{t,l} v_l \, \Delta t \, \Delta d_{l,t,s}
$$

$v_l$ is per MWh, so the adjustment (in MW) is multiplied by the timestep length $\Delta t$.

### Power balance contribution

Demand side: $\sum_l \left( d^{\text{base}}_{l,t,s} + \Delta d_{l,t,s} \right)$. See [Power balance](../concepts/power_balance.md).

## Next steps

Ready to add time-shifting to your portfolio? See [Battery](battery.md) and [StationaryStorage](stationary_storage.md).
