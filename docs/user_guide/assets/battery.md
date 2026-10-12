---
icon: fontawesome/solid/battery-three-quarters
---

# Battery

A `Battery` describes the physics of an energy store: its capacity, power limits, efficiencies, and state of charge (SOC). It is not an asset by itself. Assets *have* a battery:

- a [StationaryStorage](stationary_storage.md) is a battery at a fixed site;
- an [ElectricVehicle](electric_vehicle.md) is a battery with a trip schedule.

Everything on this page applies to both.

## Basic usage

```python
from odys import Battery, StationaryStorage

storage = StationaryStorage(
    name="bess",
    battery=Battery(
        capacity=100.0,  # MWh of storage
        max_charge_power=50.0,  # MW charge limit
        max_discharge_power=50.0,  # MW discharge limit
        efficiency_charging=0.95,
        efficiency_discharging=0.95,
        soc_start=0.5,  # starts at 50%
    ),
)
```

## Fields

| Field                    | Type            | Required | Default | Description                                                                      |
| ------------------------ | --------------- | -------- | ------- | -------------------------------------------------------------------------------- |
| `capacity`               | `float`         | Yes      | -       | Total energy capacity (MWh)                                                      |
| `max_charge_power`       | `float`         | Yes      | -       | Maximum charging power (MW)                                                      |
| `max_discharge_power`    | `float`         | Yes      | -       | Maximum discharging power (MW). Use `0` for charge-only assets                   |
| `efficiency_charging`    | `float`         | No       | `1.0`   | Charging efficiency, between 0 and 1                                             |
| `efficiency_discharging` | `float`         | No       | `1.0`   | Discharging efficiency, between 0 and 1                                          |
| `soc_start`              | `float`         | Yes      | -       | Initial state of charge, as a fraction of capacity (0-1)                         |
| `soc_end`                | `float \| None` | No       | `None`  | Required final state of charge (0-1). If `None`, the optimizer is free to choose |
| `soc_min`                | `float`         | No       | `0.0`   | Minimum allowed state of charge (0-1)                                            |
| `soc_max`                | `float`         | No       | `1.0`   | Maximum allowed state of charge (0-1)                                            |
| `degradation_cost`       | `float`         | No       | `0.0`   | Cost per MWh cycled (charged or discharged), included in the objective           |
| `self_discharge_rate`    | `float`         | No       | `0.0`   | Fractional self-discharge per hour applied in the SOC dynamics                   |

## Charge and discharge limits

The battery charges at most at `max_charge_power` and discharges at most at `max_discharge_power`. It never charges and discharges in the same timestep: doing both would be physically impossible and would create artificial efficiency losses in the model.

See the [formulation](#math-power-limits).

## State of charge (SOC)

The SOC fields control how the battery's energy level behaves:

- `soc_start` is where the battery begins. A value of `0.5` means it starts at 50% of its capacity.
- `soc_end` constrains where the battery must end up. This is useful when you want to ensure the battery isn't fully drained at the end of the optimization horizon.
- `soc_min` and `soc_max` set the operating range. For example, if you don't want to go below 20% or above 90%:

```python
battery = Battery(
    capacity=100.0,
    max_charge_power=50.0,
    max_discharge_power=50.0,
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

See the [formulation](#math-soc).

## Efficiency

Charging and discharging efficiencies are applied separately. If you charge 10 MWh with 90% efficiency, 9 MWh actually goes into the battery. If you then discharge those 9 MWh at 85% efficiency, you get 7.65 MWh out.

This means the round-trip efficiency is `efficiency_charging * efficiency_discharging`.

See the [formulation](#math-soc).

## Self-discharge

`self_discharge_rate` is the fraction of the stored energy lost per hour while the battery sits idle. A rate of `0.001` loses 0.1% of the SOC every hour.

See the [formulation](#math-soc).

## Degradation cost

`degradation_cost` models battery wear, in currency per MWh cycled. It's applied to total energy throughput; both charging and discharging count toward cycling.

```python
battery = Battery(
    capacity=100.0,
    max_charge_power=50.0,
    max_discharge_power=50.0,
    efficiency_charging=0.95,
    efficiency_discharging=0.95,
    soc_start=0.5,
    degradation_cost=5.0,  # 5 currency units per MWh cycled
)
```

This makes the optimizer weigh the value of cycling the battery against the wear it causes, discouraging unnecessary charge/discharge cycles.

See the [formulation](#math-objective).

## Results

A battery's results are read through the asset that owns it: [`result.stationary_storages`](stationary_storage.md#results) or [`result.electric_vehicles`](electric_vehicle.md#results). Both expose `net_power`, `soc`, and `charge_mode`.

## Mathematical formulation

Here $b$ is any battery-backed asset: a stationary storage or an electric vehicle. See [Mathematical notation](../mathematical_notation.md) for every symbol.

### Variables

| Symbol | Result attribute | Domain | Meaning |
| ------ | ---------------- | ------ | ------- |
| $p^{ch}_{b,t,s}$ | - | $\ge 0$ | Charging power |
| $p^{dis}_{b,t,s}$ | - | $\ge 0$ | Discharging power |
| $p^{net}_{b,t,s}$ | `net_power` | $\mathbb{R}$ | Net power, positive when charging |
| $SOC_{b,t,s}$ | `soc` | $\ge 0$ | State of charge, as a fraction of capacity |
| $z_{b,t,s}$ | `charge_mode` | $\{0,1\}$ | 1 when the battery is allowed to charge |

### Constraints

#### Charge and discharge limits {#math-power-limits}

$$
p^{ch}_{b,t,s} \le z_{b,t,s} \, P^{ch,\max}_b, \qquad
p^{dis}_{b,t,s} \le \left(1 - z_{b,t,s}\right) P^{dis,\max}_b
$$

The binary $z_{b,t,s}$ keeps the battery from charging and discharging in the same timestep.

#### State of charge {#math-soc}

For $t > 0$:

$$
SOC_{b,t,s} = SOC_{b,t-1,s} \left(1 - \delta_b \Delta t\right)
+ \eta^{ch}_b \frac{\Delta t}{E_b} p^{ch}_{b,t,s}
- \frac{\Delta t}{\eta^{dis}_b E_b} p^{dis}_{b,t,s}
$$

At the first timestep, the battery starts from $SOC^{start}_b$:

$$
SOC_{b,0,s} = SOC^{start}_b
+ \eta^{ch}_b \frac{\Delta t}{E_b} p^{ch}_{b,0,s}
- \frac{\Delta t}{\eta^{dis}_b E_b} p^{dis}_{b,0,s}
$$

The SOC stays within its operating range and, when `soc_end` is set, ends at $SOC^{end}_b$:

$$
SOC^{\min}_b \le SOC_{b,t,s} \le SOC^{\max}_b, \qquad
SOC_{b,t,s} \le 1, \qquad
SOC_{b,T,s} = SOC^{end}_b
$$

The round-trip efficiency is $\eta^{rt}_b = \eta^{ch}_b \eta^{dis}_b$. Electric vehicles also subtract trip energy in the SOC dynamics; see [ElectricVehicle](electric_vehicle.md#math-trips).

#### Net power {#math-net-power}

$$
p^{net}_{b,t,s} = p^{ch}_{b,t,s} - p^{dis}_{b,t,s}
$$

### Objective contribution {#math-objective}

The degradation cost is subtracted from the profit $\Pi_s$:

$$
- \sum_{t,b} c^{deg}_b \, \Delta t \left(p^{ch}_{b,t,s} + p^{dis}_{b,t,s}\right)
$$

### Power balance contribution

Discharging is supply ($+\sum_b p^{dis}_{b,t,s}$) and charging is demand ($\sum_b p^{ch}_{b,t,s}$). See [Power balance](../concepts/power_balance.md).

## Next steps

Put the battery in a site with [StationaryStorage](stationary_storage.md), or on the road with [ElectricVehicle](electric_vehicle.md).
