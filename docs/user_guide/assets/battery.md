---
icon: fontawesome/solid/battery-three-quarters
---

# Battery

A `Battery` describes the physics of an energy store: its capacity, power limits, efficiencies, and state of charge (SOC) limits. It is not an asset by itself. Assets *have* a battery:

- a [StationaryStorage](stationary_storage.md) is a battery at a fixed site;
- an [ElectricVehicle](electric_vehicle.md) is a battery with a trip schedule.

Everything on this page applies to both. We use composition rather than inheritance because a site battery and a vehicle battery share their physics but not their purpose: one sits on the bus, the other drives away.

Where the battery starts and ends is not part of the battery: it belongs to the run, so you pass it to the `EnergySystem` as an initial and, optionally, a final condition. See [State of charge](#state-of-charge-soc).

## Basic usage

Here is the battery of the site's `bess` from the [StationaryStorage](stationary_storage.md#basic-usage) page on its own:

```python
from odys import Battery, StationaryStorage

battery = Battery(
    capacity=50.0,  # MWh of storage
    max_charge_power=25.0,  # MW charge limit
    max_discharge_power=25.0,  # MW discharge limit
    efficiency_charging=0.95,
    efficiency_discharging=0.95,
)
bess = StationaryStorage(name="bess", battery=battery)
```

A `Battery` has no name and is never added to a portfolio: the asset that owns it is.

## Fields

| Field                    | Type            | Required | Default | Description                                                                      |
| ------------------------ | --------------- | -------- | ------- | -------------------------------------------------------------------------------- |
| `capacity`               | `float`         | Yes      | -       | Total energy capacity (MWh)                                                      |
| `max_charge_power`       | `float`         | Yes      | -       | Maximum charging power (MW)                                                      |
| `max_discharge_power`    | `float`         | Yes      | -       | Maximum discharging power (MW). Use `0` for charge-only assets                   |
| `efficiency_charging`    | `float`         | No       | `1.0`   | Charging efficiency, between 0 and 1                                             |
| `efficiency_discharging` | `float`         | No       | `1.0`   | Discharging efficiency, between 0 and 1                                          |
| `soc_min`                | `float`         | No       | `0.0`   | Minimum allowed state of charge (0-1)                                            |
| `soc_max`                | `float`         | No       | `1.0`   | Maximum allowed state of charge (0-1)                                            |
| `degradation_cost`       | `float`         | No       | `0.0`   | Cost per MWh charged or discharged (currency/MWh), included in the objective     |
| `self_discharge_rate`    | `float`         | No       | `0.0`   | Fractional self-discharge per hour applied in the SOC dynamics                   |

## Charge and discharge limits

The battery charges at most at `max_charge_power` and discharges at most at `max_discharge_power`. It never charges and discharges in the same timestep: doing both would be physically impossible and would create artificial efficiency losses in the model.

See the [formulation](#math-power-limits).

## State of charge (SOC)

Four values control how the battery's energy level behaves:

- The initial state (`StorageInitialState`, or `ElectricVehicleInitialState` for an EV) sets where the battery begins. `soc=0.5` means it starts at 50% of its capacity.
- An optional final state (`StorageFinalState` or `ElectricVehicleFinalState`) sets where the battery must end up. This is useful when you don't want it drained at the end of the horizon, so the next run can use it. Without one, the optimizer is free to choose.
- The battery's `soc_min` and `soc_max` set the operating range. For example, if you don't want to go below 20% or above 90%:

```python
from odys import StorageFinalState, StorageInitialState

bess = StationaryStorage(
    name="bess",
    battery=Battery(
        capacity=50.0,
        max_charge_power=25.0,
        max_discharge_power=25.0,
        efficiency_charging=0.95,
        efficiency_discharging=0.95,
        soc_min=0.2,
        soc_max=0.9,
    ),
)
initial_conditions = (StorageInitialState(storage=bess, soc=0.5),)
final_conditions = (StorageFinalState(storage=bess, soc=0.5),)
```

!!! note

    The initial and final state of charge must fall within the battery's `[soc_min, soc_max]` range. Creating the state raises an `OdysValidationError` if it doesn't.

See [Initial and final conditions](../concepts/initial_and_final_conditions.md#storage-and-electric-vehicles) for every field, and the [formulation](#math-soc).

## Efficiency

Charging and discharging efficiencies are applied separately. If you charge 10 MWh with 90% efficiency, 9 MWh actually goes into the battery. If you then discharge those 9 MWh at 85% efficiency, you get 7.65 MWh out.

This means the round-trip efficiency is `efficiency_charging * efficiency_discharging`.

See the [formulation](#math-soc).

## Self-discharge

`self_discharge_rate` is the fraction of the stored energy lost per hour while the battery sits idle. A rate of `0.001` loses 0.1% of the SOC every hour, from the first step on.

See the [formulation](#math-soc).

## Degradation cost

`degradation_cost` models battery wear, in currency per MWh cycled. It's applied to total energy throughput; both charging and discharging count toward cycling.

```python
battery = Battery(
    capacity=50.0,
    max_charge_power=25.0,
    max_discharge_power=25.0,
    efficiency_charging=0.95,
    efficiency_discharging=0.95,
    degradation_cost=5.0,  # 5 currency units per MWh cycled
)
```

This makes the optimizer weigh the value of cycling the battery against the wear it causes, discouraging unnecessary charge/discharge cycles.

See the [formulation](#math-objective).

## Results

A battery's results are read through the asset that owns it: [`result.stationary_storages`](stationary_storage.md#results) or [`result.electric_vehicles`](electric_vehicle.md#results). Both expose `net_power` (MW, positive when charging), `soc` (fraction of capacity) and `charge_mode`.

See the [Battery Dispatch example](../../examples/battery_dispatch.md) for a battery storing solar output over a full day.

## Mathematical formulation

Here $b$ is any battery-backed asset: a stationary storage or an electric vehicle.

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

At the first timestep, the battery starts from its initial state of charge $SOC^{start}_b$:

$$
SOC_{b,0,s} = SOC^{start}_b \left(1 - \delta_b \Delta t\right)
+ \eta^{ch}_b \frac{\Delta t}{E_b} p^{ch}_{b,0,s}
- \frac{\Delta t}{\eta^{dis}_b E_b} p^{dis}_{b,0,s}
$$

The SOC stays within its operating range and, when the battery has a final state, ends at $SOC^{end}_b$:

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

Next, let's put a battery on the road: see [ElectricVehicle](electric_vehicle.md).
