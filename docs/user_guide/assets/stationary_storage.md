---
icon: fontawesome/solid/car-battery
---

# StationaryStorage

A `StationaryStorage` models a stationary energy storage system in your portfolio, such as a grid-scale battery. The optimizer decides when to charge and discharge it to minimize costs (or maximize revenue).

A storage asset *has* a [Battery](battery.md): the asset is the site you own, and the battery describes its physics (capacity, power limits, efficiencies, state of charge).

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

| Field     | Type      | Required | Default | Description                                         |
| --------- | --------- | -------- | ------- | --------------------------------------------------- |
| `name`    | `str`     | Yes      | -       | Unique identifier for the storage                   |
| `battery` | `Battery` | Yes      | -       | The battery's physics; see [Battery](battery.md#fields) |

SOC limits, efficiencies, self-discharge, and degradation cost are all set on the `Battery`. See [Battery](battery.md).

## Initial and final state

Where the storage starts and ends belongs to the run, not to the battery. Pass a `StorageInitialState` (required) and, optionally, a `StorageFinalState` to the `EnergySystem`:

| Class                 | Field     | Type                | Description                                |
| --------------------- | --------- | ------------------- | ------------------------------------------ |
| `StorageInitialState` | `storage` | `StationaryStorage` | The storage                                |
|                       | `soc`     | `float`             | State of charge just before the first step |
| `StorageFinalState`   | `storage` | `StationaryStorage` | The storage                                |
|                       | `soc`     | `float`             | State of charge at the last step           |

See [Battery](battery.md#state-of-charge-soc) for how they shape the state of charge, and the [formulation](battery.md#math-soc).

## Results

After optimization, access storage results through `result.stationary_storages`:

```python
result = energy_system.optimize()

result.stationary_storages.net_power  # charge/discharge per timestep
result.stationary_storages.soc  # SOC at each timestep (fraction of capacity)
result.stationary_storages.charge_mode  # binary charging mode
```

Positive `net_power` means charging, negative means discharging.

## Mathematical formulation

A stationary storage adds nothing to the [Battery formulation](battery.md#mathematical-formulation): its variables, constraints, degradation cost, and power balance terms are exactly those of its battery, with $b$ ranging over the stationary storages.

## Next steps

Need mobile storage with trip schedules? See [ElectricVehicle](electric_vehicle.md). Want to buy or sell energy from external markets? See [EnergyMarket](../markets/energy_market.md).
