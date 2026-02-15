# Battery

A `Battery` models an energy storage system in your portfolio. The optimizer decides when to charge and discharge it to minimize costs (or maximize revenue).

## Basic usage

```python
from odys.energy_system_models.assets.storage import Battery

battery = Battery(
    name="bess",
    capacity=100.0,          # MWh of storage
    max_power=50.0,           # MW charge/discharge limit
    efficiency_charging=0.95,
    efficiency_discharging=0.95,
    soc_start=0.5,            # starts at 50%
)
```

## Fields

| Field                    | Type    | Required | Default | Description                                                                      |
| ------------------------ | ------- | -------- | ------- | -------------------------------------------------------------------------------- |
| `name`                   | `str`   | Yes      | -       | Unique identifier for the battery                                                |
| `capacity`               | `float` | Yes      | -       | Total energy capacity (MWh)                                                      |
| `max_power`              | `float` | Yes      | -       | Maximum charge/discharge power (MW)                                              |
| `efficiency_charging`    | `float` | Yes      | -       | Charging efficiency, between 0 and 1                                             |
| `efficiency_discharging` | `float` | Yes      | -       | Discharging efficiency, between 0 and 1                                          |
| `soc_start`              | `float` | Yes      | -       | Initial state of charge, as a fraction of capacity (0-1)                         |
| `soc_end`                | `float` | No       | `None`  | Required final state of charge (0-1). If `None`, the optimizer is free to choose |
| `soc_min`                | `float` | No       | `0.0`   | Minimum allowed state of charge (0-1)                                            |
| `soc_max`                | `float` | No       | `1.0`   | Maximum allowed state of charge (0-1)                                            |
| `degradation_cost`       | `float` | No       | `None`  | Cost per MWh cycled through the battery                                          |
| `self_discharge_rate`    | `float` | No       | `None`  | Fraction of stored energy lost per hour (0-1)                                    |

## State of charge (SOC)

The SOC fields control how the battery's energy level behaves:

- `soc_start` is where the battery begins. A value of `0.5` means it starts at 50% of its capacity.
- `soc_end` constrains where the battery must end up. This is useful when you want to ensure the battery isn't fully drained at the end of the optimization horizon.
- `soc_min` and `soc_max` set the operating range. For example, if you don't want to go below 20% or above 90%:

```python
battery = Battery(
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

## Efficiency

Charging and discharging efficiencies are applied separately. If you charge 10 MWh with 90% efficiency, 9 MWh actually goes into the battery. If you then discharge those 9 MWh at 85% efficiency, you get 7.65 MWh out.

This means the round-trip efficiency is `efficiency_charging * efficiency_discharging`.

## Degradation cost

If you want the optimizer to account for battery wear, set a `degradation_cost`:

```python
battery = Battery(
    name="bess",
    capacity=100.0,
    max_power=50.0,
    efficiency_charging=0.95,
    efficiency_discharging=0.95,
    soc_start=0.5,
    degradation_cost=5.0,  # 5 currency units per MWh cycled
)
```

This adds a cost penalty for each MWh that flows through the battery, discouraging unnecessary cycling.

## Results

After optimization, access battery results through `result.batteries`:

```python
result = energy_system.optimize()

result.batteries.net_power        # charge/discharge per timestep
result.batteries.state_of_charge  # SOC at each timestep
```

Positive `net_power` means discharging, negative means charging.
