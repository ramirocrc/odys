---
icon: fontawesome/solid/car-battery
---

# BatteryStorage

A `BatteryStorage` models a battery at a fixed, grid-connected site: a battery energy storage system (BESS), with a fixed capacity, charge and discharge limits, efficiencies and self-discharge. Closed-loop pumped hydro fits it as a first approximation, as long as you can leave out natural inflow, a minimum pumping or generating power, and start costs.

A battery storage *has* a [Battery](battery.md): the asset is what you own and name, and the battery holds all its physics. This page covers what the asset adds; the [Battery](battery.md) page covers everything else.

## Basic usage

Let's add a battery to the site: 50 MWh that charges and discharges at up to 25 MW, starting half full.

```python
from odys import Battery, BatteryStorage, StorageInitialState

bess = BatteryStorage(
    name="bess",
    battery=Battery(
        capacity=50.0,  # MWh of storage
        max_charge_power=25.0,  # MW charge limit
        max_discharge_power=25.0,  # MW discharge limit
        efficiency_charging=0.95,
        efficiency_discharging=0.95,
    ),
)
starts_half_full = StorageInitialState(storage=bess, soc=0.5)
```

Add `bess` to your [AssetPortfolio](../model/first_model.md#the-portfolio), and pass `starts_half_full` to the `EnergySystem` with `initial_conditions=(starts_half_full,)`.

## Fields

| Field     | Type      | Required | Default | Description                                              |
| --------- | --------- | -------- | ------- | -------------------------------------------------------- |
| `name`    | `str`     | Yes      | -       | Unique name of the storage                               |
| `battery` | `Battery` | Yes      | -       | Its capacity, ratings and losses; see [Battery](battery.md#fields) |

## Initial and final state

A battery storage takes a `StorageInitialState`, which is required, and optionally a `StorageFinalState`. Both take the storage and its state of charge, `soc`, as a fraction of capacity. How they shape the plan, and their fields, are on the Battery page, under [State of charge](battery.md#state-of-charge).

## Results

A battery storage's results are in `result.battery_storages`: `net_power`, `soc` and `charge_mode`, one `pandas.Series` each. The Battery page solves the site with its battery and shows how to read them, under [Results](battery.md#results). The [Storing Solar for the Evening](../../examples/solar_storage.md) example runs a battery through a full day of solar.

## How it's modelled

A battery storage is a battery on the bus, with no rules of its own: the battery's [B-1](../../formulation/batteries.md#b-1) to [B-7](../../formulation/batteries.md#b-7). It charges from the [power balance](../../formulation/power_balance.md#pb-1) and discharges into it, and its wear enters the [objective](../../formulation/batteries.md#objective-contribution).

## Next steps

Some batteries drive away. Next, see how an [ElectricVehicle](electric_vehicle.md) adds trips to a battery.
