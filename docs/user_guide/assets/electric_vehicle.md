---
icon: fontawesome/solid/car
---

# ElectricVehicle

An `ElectricVehicle` models a vehicle in a fleet: a [Battery](battery.md) that leaves on trips. While it's parked and plugged in, it charges, and with vehicle-to-grid (V2G) it can also feed power back, always through a [Charger](charger.md). The optimizer decides when each vehicle charges and discharges, so that every trip leaves with enough charge at the lowest cost.

A fleet is a much smaller scale than the site of the [running example](../index.md#the-running-example), so this page and the [Charger](charger.md) page use a depot of two delivery vans over a 12-hour shift, in hourly steps from 06:00. Powers and energies are still in MW and MWh, so a 22 kW charger is `0.022`.

## Basic usage

```python
from datetime import timedelta

from odys import Battery, ElectricVehicle, ElectricVehicleFinalState, ElectricVehicleInitialState, Trip

van_1 = ElectricVehicle(
    name="van_1",
    battery=Battery(
        capacity=0.100,  # 100 kWh
        max_charge_power=0.022,  # 22 kW
        max_discharge_power=0.011,  # 11 kW V2G
        efficiency_charging=0.95,
        efficiency_discharging=0.95,
    ),
    trips=(
        Trip(
            name="morning_delivery",
            start_time=timedelta(hours=2),  # leaves at 08:00
            end_time=timedelta(hours=4),  # back at 10:00
            energy_consumption=0.030,  # 30 kWh
            min_soc_at_departure=0.8,
        ),
    ),
)
initial_conditions = (ElectricVehicleInitialState(vehicle=van_1, soc=0.5),)
final_conditions = (ElectricVehicleFinalState(vehicle=van_1, soc=0.5),)
```

`van_1` starts the shift half charged, has to leave at 08:00 with at least 80 %, and has to be back at 50 % at the end of the shift. Both states go to the `EnergySystem`, with `initial_conditions=...` and `final_conditions=...` (see [Initial and final state](#initial-and-final-state)).

## Fields

| Field     | Type               | Required | Default | Description                                                      |
| --------- | ------------------ | -------- | ------- | ---------------------------------------------------------------- |
| `name`    | `str`              | Yes      | -       | Unique name of the vehicle                                       |
| `battery` | `Battery`          | Yes      | -       | Its capacity, ratings and losses; see [Battery](battery.md#fields) |
| `trips`   | `tuple[Trip, ...]` | Yes      | -       | Its trips over the run; `()` for a vehicle that stays at the depot |

## Vehicle-to-grid (V2G)

The battery's `max_discharge_power` decides whether a vehicle can feed power back. Above 0, it can discharge, at up to that power; at `0.0`, it can only charge. Either way, power flows only while the vehicle is connected to a charger, so V2G goes through the charger too. `van_1` above can give back up to 11 kW. See [B-2](../../formulation/batteries.md#b-2) and [CH-4](../../formulation/electric_vehicles.md#ch-4).

## Trips

A `Trip` says when the vehicle is away, how much energy it uses, and how full it has to be when it leaves:

| Field                  | Type        | Required | Default | Description                                                              |
| ---------------------- | ----------- | -------- | ------- | ------------------------------------------------------------------------ |
| `name`                 | `str`       | Yes      | -       | Name of the trip                                                          |
| `start_time`           | `timedelta` | Yes      | -       | When the vehicle leaves, counted from the start of the run               |
| `end_time`             | `timedelta` | Yes      | -       | When it's back, counted from the start of the run; after `start_time`    |
| `energy_consumption`   | `float`     | Yes      | -       | Energy the battery provides for the trip, after drivetrain losses, above 0 (MWh) |
| `min_soc_at_departure` | `float`     | No       | `0.0`   | Lowest state of charge when the vehicle leaves, as a fraction of capacity |

Trip times count from the start of the run, not from a clock time. With the shift starting at 06:00, a second van's afternoon route from 12:00 to 15:00 starts 6 hours in and ends 9 hours in:

```python
van_2 = ElectricVehicle(
    name="van_2",
    battery=Battery(
        capacity=0.100,
        max_charge_power=0.022,
        max_discharge_power=0.011,
        efficiency_charging=0.95,
        efficiency_discharging=0.95,
    ),
    trips=(
        Trip(
            name="afternoon_route",
            start_time=timedelta(hours=6),
            end_time=timedelta(hours=9),
            energy_consumption=0.040,
            min_soc_at_departure=0.7,
        ),
    ),
)
```

Here's what a trip means for the plan:

- The vehicle is away from `start_time` until `end_time`. In that time it can't charge, discharge, or hold a charger, and it can charge again from the step that starts at `end_time`.
- The trip's energy leaves the battery evenly over the steps it's away: `van_2`'s 40 kWh over three steps is 0.133 of its capacity per step.
- The battery has at least `min_soc_at_departure` when the vehicle leaves, before the trip uses any energy. It also stays above `soc_min` while driving, so a trip has to fit in the charge the vehicle can leave with.
- Trips of one vehicle can't overlap; building the vehicle raises an `OdysValidationError` if they do. Trip times also have to fall on a step and end within the run, which is checked when you create the `EnergySystem`: with 15-minute steps, a trip can leave at 45 minutes but not at 50.

See [EV-1](../../formulation/electric_vehicles.md#ev-1) to [EV-3](../../formulation/electric_vehicles.md#ev-3) and [CH-3](../../formulation/electric_vehicles.md#ch-3).

## Initial and final state

A vehicle takes an `ElectricVehicleInitialState`, which is required, and optionally an `ElectricVehicleFinalState`. They work like any battery's, under [State of charge](battery.md#state-of-charge).

One check is particular to vehicles: a trip that leaves at the very start of the run (`start_time=timedelta(0)`) has no step before it to charge in. So creating the `ElectricVehicleInitialState` raises an `OdysValidationError` when the starting charge can't serve that trip, because it's below the trip's `min_soc_at_departure`, or holds less energy above `soc_min` than the trip uses.

Their fields are on the Battery page, under [State of charge](battery.md#state-of-charge).

## Results

A vehicle's results are in `result.electric_vehicles`: `net_power`, `soc` and `charge_mode`, one `pandas.Series` each, indexed by vehicle and time. They read like any battery's, under [Results](battery.md#results). The vans can't charge yet, so the depot is solved on the [Charger](charger.md#results) page, once it has one. The [EV Fleet example](../../examples/ev_fleet_optimization.md) runs three vans and two chargers over a full day.

## How it's modelled

A vehicle is a battery, [B-1](../../formulation/batteries.md#b-1) to [B-7](../../formulation/batteries.md#b-7), plus its trips: [EV-1](../../formulation/electric_vehicles.md#ev-1) takes the trip's energy out of the battery, [EV-2](../../formulation/electric_vehicles.md#ev-2) stops charging on the road, and [EV-3](../../formulation/electric_vehicles.md#ev-3) checks the charge at departure. Its power reaches the bus only through a charger ([CH-1](../../formulation/electric_vehicles.md#ch-1) to [CH-4](../../formulation/electric_vehicles.md#ch-4)). Every rule and its limitations are on the [Electric vehicles and chargers](../../formulation/electric_vehicles.md) formulation page.

## Next steps

The vans can't charge yet: they need a charger. Next, see how a [Charger](charger.md) connects them to the grid, and solve the depot's day.
