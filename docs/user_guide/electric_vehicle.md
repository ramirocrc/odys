---
icon: fontawesome/solid/car
---

# ElectricVehicle

An `ElectricVehicle` is a storage asset with trip schedules. It inherits all battery physics from storage and adds constraints that make the vehicle unavailable for charging while driving and consume energy during trips.

Unlike a stationary [StandaloneStorage](storage.md), EVs must connect through a [Charger](charger.md) to charge or discharge. With more EVs than chargers, the optimizer assigns vehicles to chargers dynamically.

See [Mathematical notation](mathematical_notation.md) for the full list of symbols used below.

## Basic usage

```python
from odys import ElectricVehicle, Trip

ev = ElectricVehicle(
    name="ev_1",
    capacity=0.100,  # 100 kWh
    max_charge_power=0.022,  # 22 kW
    max_discharge_power=0.011,  # 11 kW V2G
    soc_start=0.8,
    soc_end=0.3,
    trips=(
        Trip(
            name="morning_delivery",
            start_time=7,
            end_time=9,
            energy_consumption=0.015,  # 15 kWh
            min_soc_at_departure=0.6,
        ),
    ),
)
```

`max_discharge_power` is what enables V2G. Without it (or with value `0`), the vehicle can only charge. `min_soc_at_departure` guarantees the vehicle has enough charge before each trip.

## Fields

`ElectricVehicle` inherits all fields from storage and adds trips:

| Field                    | Type               | Required | Default | Description                                                    |
| ------------------------ | ------------------ | -------- | ------- | -------------------------------------------------------------- |
| `name`                   | `str`              | Yes      | -       | Unique identifier for the EV                                   |
| `capacity`               | `float`            | Yes      | -       | Battery capacity (MWh)                                         |
| `max_charge_power`       | `float`            | Yes      | -       | Maximum charging power (MW)                                    |
| `max_discharge_power`    | `float`            | Yes      | -       | Maximum discharging power (MW). Use `0` for charge-only        |
| `efficiency_charging`    | `float`            | No       | `1.0`   | Charging efficiency (0-1)                                      |
| `efficiency_discharging` | `float`            | No       | `1.0`   | Discharging efficiency (0-1)                                   |
| `soc_start`              | `float`            | Yes      | -       | Initial state of charge (0-1)                                  |
| `soc_end`                | `float`            | No       | `None`  | Required final state of charge (0-1)                           |
| `soc_min`                | `float`            | No       | `0.0`   | Minimum allowed state of charge (0-1)                          |
| `soc_max`                | `float`            | No       | `1.0`   | Maximum allowed state of charge (0-1)                          |
| `degradation_cost`       | `float`            | No       | `0.0`   | Cost per MWh cycled                                            |
| `self_discharge_rate`    | `float`            | No       | `0.0`   | Fractional self-discharge per hour                             |
| `trips`                  | `tuple[Trip, ...]` | Yes      | -       | Trip schedule. Can be empty if the EV stays at the depot       |

## Trips

A `Trip` defines when the vehicle is driving, how much energy it consumes, and the minimum SoC required at departure:

| Field                | Type    | Required | Default | Description                                                         |
| -------------------- | ------- | -------- | ------- | ------------------------------------------------------------------- |
| `name`               | `str`   | Yes      | -       | Unique trip name within the vehicle                                 |
| `start_time`         | `int`   | Yes      | -       | Timestep index when the trip starts                                 |
| `end_time`           | `int`   | Yes      | -       | Timestep index when the trip ends (`end_time > start_time`)         |
| `energy_consumption` | `float` | Yes      | -       | Battery-side energy consumed during the trip (MWh)                  |
| `min_soc_at_departure` | `float` | No     | `0.0`   | Minimum SoC required at departure, before trip energy is consumed   |

While a trip is active, the EV cannot charge, discharge, or be assigned to a charger. Trip energy is subtracted from the battery SoC during the trip window.

```python
Trip(
    name="midday_route",
    start_time=12,
    end_time=13,
    energy_consumption=0.006,
    min_soc_at_departure=0.35,
)
```

## Constraints

In addition to the shared storage physics (SOC dynamics, charge/discharge limits, efficiencies), EVs add:

1. **Driving unavailability**: no charge or discharge while driving
2. **Departure SoC**: SoC must meet `min_soc_at_departure` by the end of the step before departure
3. **Charger coupling**: charge and discharge power are limited by the assigned charger's `max_power` (see [Charger](charger.md))

## Results

After optimization, access EV results through `result.electric_vehicles`:

```python
result = energy_system.optimize()

result.electric_vehicles.net_power  # positive = charging, negative = discharging
result.electric_vehicles.soc  # state of charge (fraction of capacity)
result.electric_vehicles.charge_mode  # binary charging mode
```

## Next steps

EVs need chargers to connect to the grid. See [Charger](charger.md) for assignment and power limits, or the [EV Fleet example](../examples/ev_fleet_optimization.md) for a full worked scenario.
