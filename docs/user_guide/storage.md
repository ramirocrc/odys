---
icon: fontawesome/solid/battery-three-quarters
---

# StationaryStorage

A `StationaryStorage` models a stationary energy storage system in your portfolio. The optimizer decides when to charge and discharge it to minimize costs (or maximize revenue).

A storage asset *has* a `Battery`: the asset is the site you own, and the battery describes its physics (capacity, power limits, efficiencies, state of charge limits). An [ElectricVehicle](electric_vehicle.md) uses the same `Battery`, so everything on this page about batteries applies to EVs too.

Where the storage starts and ends is not part of the battery: it belongs to the run, so you pass it to the `EnergySystem` as a `StorageInitialState` and, optionally, a `StorageFinalState`.

See [Mathematical notation](mathematical_notation.md) for the full list of symbols used below.

## Basic usage

Let's add a battery to the portfolio.

```python
from odys import Battery, StationaryStorage, StorageInitialState

storage = StationaryStorage(
    name="bess",
    battery=Battery(
        capacity=100.0,  # MWh of storage
        max_charge_power=50.0,  # MW charge limit
        max_discharge_power=50.0,  # MW discharge limit
        efficiency_charging=0.95,
        efficiency_discharging=0.95,
    ),
)
starts_half_full = StorageInitialState(storage=storage, soc=0.5)
```

Pass `starts_half_full` to the energy system with `EnergySystem(..., initial_conditions=(starts_half_full,))`. Every storage needs an initial state: its state of charge carries over from one step to the next, so odys never guesses where it starts.

## Fields

`StationaryStorage` has two fields:

| Field     | Type      | Required | Default | Description                       |
| --------- | --------- | -------- | ------- | --------------------------------- |
| `name`    | `str`     | Yes      | -       | Unique identifier for the storage |
| `battery` | `Battery` | Yes      | -       | The battery's physics (see below) |

`Battery` fields:

| Field                    | Type    | Required | Default | Description                                                                      |
| ------------------------ | ------- | -------- | ------- | -------------------------------------------------------------------------------- |
| `capacity`               | `float` | Yes      | -       | Total energy capacity (MWh)                                                      |
| `max_charge_power`       | `float` | Yes      | -       | Maximum charging power (MW)                                                      |
| `max_discharge_power`    | `float` | Yes      | -       | Maximum discharging power (MW). Use `0` for charge-only assets                   |
| `efficiency_charging`    | `float` | No       | `1.0`   | Charging efficiency, between 0 and 1                                             |
| `efficiency_discharging` | `float` | No       | `1.0`   | Discharging efficiency, between 0 and 1                                          |
| `soc_min`                | `float` | No       | `0.0`   | Minimum allowed state of charge (0-1)                                            |
| `soc_max`                | `float` | No       | `1.0`   | Maximum allowed state of charge (0-1)                                            |
| `degradation_cost`       | `float` | No       | `0.0`   | Cost per MWh cycled (charged or discharged), included in the objective          |
| `self_discharge_rate`    | `float` | No       | `0.0`   | Fractional self-discharge per hour applied in the SOC dynamics                   |

## State of charge (SOC)

Four values control how the storage's energy level behaves:

- The `StorageInitialState` sets where the storage begins. `soc=0.5` means it starts at 50% of its capacity.
- An optional `StorageFinalState` sets where the storage must end up. This is useful when you don't want the storage drained at the end of the horizon, so the next run can use it. Without one, the optimizer is free to choose.
- The battery's `soc_min` and `soc_max` set the operating range. For example, if you don't want to go below 20% or above 90%:

```python
from odys import StorageFinalState

storage = StationaryStorage(
    name="bess",
    battery=Battery(
        capacity=100.0,
        max_charge_power=50.0,
        max_discharge_power=50.0,
        efficiency_charging=0.90,
        efficiency_discharging=0.85,
        soc_min=0.2,
        soc_max=0.9,
    ),
)
initial_conditions = (StorageInitialState(storage=storage, soc=0.5),)
final_conditions = (StorageFinalState(storage=storage, soc=0.5),)
```

!!! note

    The initial and final state of charge must fall within the battery's `[soc_min, soc_max]` range. Creating the state raises an `OdysValidationError` if it doesn't.

The SOC evolution is:

$$
0 \le p^{ch}_{b,t}, \qquad 0 \le p^{dis}_{b,t}, \qquad 0 \le SOC_{b,t}, \qquad z_{b,t} \in \{0,1\}
$$

$$
SOC_{b,t} = SOC_{b,t-1} (1 - \delta_b \Delta t)
+ \eta^{ch}_b \frac{\Delta t}{E_b} p^{ch}_{b,t}
- \frac{\Delta t}{\eta^{dis}_b E_b} p^{dis}_{b,t}
$$

for $t > 0$, where $\delta_b$ is the self-discharge rate. At the first timestep, the implementation starts from the initial state of charge $SOC^{start}_b$:

$$
SOC_{b,0} = SOC^{start}_b
+ \eta^{ch}_b \frac{\Delta t}{E_b} p^{ch}_{b,0}
- \frac{\Delta t}{\eta^{dis}_b E_b} p^{dis}_{b,0}
$$

When the storage has a final state, its state of charge at the last step is fixed:

$$
SOC_{b,T-1} = SOC^{end}_b
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
p^{ch}_{b,t} \le z_{b,t} P^{ch,\max}_b
$$

$$
p^{dis}_{b,t} + z_{b,t} P^{dis,\max}_b \le P^{dis,\max}_b
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

`Battery` accepts a `degradation_cost` field modeling battery wear, in currency per MWh cycled. It's applied to total energy throughput; both charging and discharging count toward cycling, and included in the objective as:

$$
C^{degradation}_{b,t} = c^{deg}_b \, \Delta t \, (p^{ch}_{b,t} + p^{dis}_{b,t})
$$

```python
storage = StationaryStorage(
    name="bess",
    battery=Battery(
        capacity=100.0,
        max_charge_power=50.0,
        max_discharge_power=50.0,
        efficiency_charging=0.95,
        efficiency_discharging=0.95,
        degradation_cost=5.0,  # 5 currency units per MWh cycled
    ),
)
```

This makes the optimizer weigh the value of cycling the battery against the wear it causes, discouraging unnecessary charge/discharge cycles.

## Results

After optimization, access storage results through `result.stationary_storages`:

```python
result = energy_system.optimize()

result.stationary_storages.net_power  # charge/discharge per timestep
result.stationary_storages.soc  # SOC at each timestep (fraction of capacity)
result.stationary_storages.charge_mode  # binary charging mode
```

The implementation defines `net_power` as:

$$
p^{net}_{b,t} = p^{ch}_{b,t} - p^{dis}_{b,t}
$$

Positive `net_power` means charging, negative means discharging.

## Next steps

Need mobile storage with trip schedules? See [ElectricVehicle](electric_vehicle.md). Want to buy or sell energy from external markets? See [Market](market.md).
