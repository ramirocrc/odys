---
icon: fontawesome/solid/battery-three-quarters
---

# Storage

A `Storage` models an energy storage system in your portfolio. The optimizer decides when to charge and discharge it to minimize costs (or maximize revenue).

See [Mathematical notation](mathematical_notation.md) for the full list of symbols used below.

## Basic usage

Let's add a battery to the portfolio.

```python
from odys import Storage

storage = Storage(
    name="bess",
    capacity=100.0,  # MWh of storage
    max_power=50.0,  # MW charge/discharge limit
    efficiency_charging=0.95,
    efficiency_discharging=0.95,
    soc_start=0.5,  # starts at 50%
)
```

## Fields

| Field                    | Type    | Required | Default | Description                                                                      |
| ------------------------ | ------- | -------- | ------- | -------------------------------------------------------------------------------- |
| `name`                   | `str`   | Yes      | -       | Unique identifier for the storage                                                |
| `capacity`               | `float` | Yes      | -       | Total energy capacity (MWh)                                                      |
| `max_power`              | `float` | Yes      | -       | Maximum charge/discharge power (MW)                                              |
| `efficiency_charging`    | `float` | Yes      | -       | Charging efficiency, between 0 and 1                                             |
| `efficiency_discharging` | `float` | Yes      | -       | Discharging efficiency, between 0 and 1                                          |
| `soc_start`              | `float` | Yes      | -       | Initial state of charge, as a fraction of capacity (0-1)                         |
| `soc_end`                | `float` | No       | `None`  | Required final state of charge (0-1). If `None`, the optimizer is free to choose |
| `soc_min`                | `float` | No       | `0.0`   | Minimum allowed state of charge (0-1)                                            |
| `soc_max`                | `float` | No       | `1.0`   | Maximum allowed state of charge (0-1)                                            |
| `degradation_cost`       | `float` | No       | `None`  | Accepted by the model object, but not included in the current objective          |
| `self_discharge_rate`    | `float` | No       | `None`  | Accepted by the model object, but not included in the current storage dynamics   |

## State of charge (SOC)

The SOC fields control how the storage's energy level behaves:

- `soc_start` is where the storage begins. A value of `0.5` means it starts at 50% of its capacity.
- `soc_end` constrains where the storage must end up. This is useful when you want to ensure the storage isn't fully drained at the end of the optimization horizon.
- `soc_min` and `soc_max` set the operating range. For example, if you don't want to go below 20% or above 90%:

```python
storage = Storage(
    name="bess",
    capacity=100.0,
    max_power=50.0,
    efficiency_charging=0.90,
    efficiency_discharging=0.85,
    soc_start=0.5,
    soc_end=0.5,
    soc_min=0.2,
    soc_max=0.9,
)
```

!!! note

    `soc_start` and `soc_end` must fall within the `[soc_min, soc_max]` range. Pydantic validation will catch this if you get it wrong.

The SOC evolution is:

$$
0 \le p^{ch}_{b,t}, \qquad 0 \le p^{dis}_{b,t}, \qquad 0 \le SOC_{b,t}, \qquad z_{b,t} \in \{0,1\}
$$

$$
SOC_{b,t} = SOC_{b,t-1}
+ \eta^{ch}_b \frac{\Delta t}{E_b} p^{ch}_{b,t}
- \frac{\Delta t}{\eta^{dis}_b E_b} p^{dis}_{b,t}
$$

for $t > 0$. At the first timestep, the implementation applies:

$$
SOC_{b,0} = SOC^{start}_b
+ \eta^{ch}_b \frac{\Delta t}{E_b} p^{ch}_{b,0}
- \frac{\Delta t}{\eta^{dis}_b E_b} p^{dis}_{b,0}
$$

with bounds:

$$
SOC^{min}_b \le SOC_{b,t} \le SOC^{max}_b
$$

and:

$$
SOC_{b,t} \le 1
$$

Charge and discharge power are constrained by the charging mode:

$$
p^{ch}_{b,t} \le z_{b,t} P^{\max}_b
$$

$$
p^{dis}_{b,t} + z_{b,t} P^{\max}_b \le P^{\max}_b
$$

Notice the binary variable $z_{b,t}$. We use it to prevent the storage from charging and discharging simultaneously, which would be physically impossible and would create artificial efficiency losses in the model.

## Efficiency

Charging and discharging efficiencies are applied separately. If you charge 10 MWh with 90% efficiency, 9 MWh actually goes into the storage. If you then discharge those 9 MWh at 85% efficiency, you get 7.65 MWh out.

This means the round-trip efficiency is `efficiency_charging * efficiency_discharging`.

In other words:

$$
\eta^{rt}_b = \eta^{ch}_b \eta^{dis}_b
$$

## Degradation cost

`Storage` accepts a `degradation_cost` field, but the current optimization objective does not include a degradation-cost term.

```python
storage = Storage(
    name="bess",
    capacity=100.0,
    max_power=50.0,
    efficiency_charging=0.95,
    efficiency_discharging=0.95,
    soc_start=0.5,
    degradation_cost=5.0,  # 5 currency units per MWh cycled
)
```

## Results

After optimization, access storage results through `result.storages`:

```python
result = energy_system.optimize()

result.storages.net_power  # charge/discharge per timestep
result.storages.state_of_charge  # SOC at each timestep
```

The implementation defines `net_power` as:

$$
p^{net}_{b,t} = p^{ch}_{b,t} - p^{dis}_{b,t}
$$

Positive `net_power` means charging, negative means discharging.

## Next steps

Want to buy or sell energy from external markets? See [Market](market.md) to add trading to your portfolio.
