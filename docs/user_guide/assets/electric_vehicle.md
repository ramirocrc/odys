---
icon: fontawesome/solid/car
---

# ElectricVehicle

An `ElectricVehicle` is an electric vehicle: it has a [Battery](battery.md) and a trip schedule. Trips make the vehicle unavailable for charging while driving and consume energy from the battery.

Unlike a [StationaryStorage](stationary_storage.md), EVs must connect through a [Charger](charger.md) to charge or discharge. With more EVs than chargers, the optimizer assigns vehicles to chargers dynamically.

## Basic usage

```python
from odys import Battery, ElectricVehicle, ElectricVehicleFinalState, ElectricVehicleInitialState, Trip

ev = ElectricVehicle(
    name="ev_1",
    battery=Battery(
        capacity=0.100,  # 100 kWh
        max_charge_power=0.022,  # 22 kW
        max_discharge_power=0.011,  # 11 kW V2G
    ),
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
initial_conditions = (ElectricVehicleInitialState(vehicle=ev, soc=0.8),)
final_conditions = (ElectricVehicleFinalState(vehicle=ev, soc=0.3),)
```

The vehicle starts at 80% and must end the day at 30%. Pass both to the `EnergySystem` (`initial_conditions=...`, `final_conditions=...`). See [Initial and final state](#initial-and-final-state).

## Fields

| Field     | Type               | Required | Default | Description                                                     |
| --------- | ------------------ | -------- | ------- | --------------------------------------------------------------- |
| `name`    | `str`              | Yes      | -       | Unique identifier for the EV                                    |
| `battery` | `Battery`          | Yes      | -       | The vehicle's battery; see [Battery](battery.md#fields)         |
| `trips`   | `tuple[Trip, ...]` | Yes      | -       | Trip schedule. Can be empty if the EV stays at the depot        |

## Vehicle-to-grid (V2G)

The battery's `max_discharge_power` is what enables V2G. Without it (or with value `0`), the vehicle can only charge. Like charging, discharging only happens through a [Charger](charger.md).

See the [Battery formulation](battery.md#math-power-limits).

## Trips

A `Trip` defines when the vehicle is driving, how much energy it consumes, and the minimum SoC required at departure:

| Field                  | Type    | Required | Default | Description                                                       |
| ---------------------- | ------- | -------- | ------- | ----------------------------------------------------------------- |
| `name`                 | `str`   | Yes      | -       | Unique trip name within the vehicle                               |
| `start_time`           | `int`   | Yes      | -       | Timestep index when the trip starts                               |
| `end_time`             | `int`   | Yes      | -       | Timestep index when the trip ends (`end_time > start_time`)       |
| `energy_consumption`   | `float` | Yes      | -       | Battery-side energy consumed during the trip (MWh)                |
| `min_soc_at_departure` | `float` | No       | `0.0`   | Minimum SoC required at departure, before trip energy is consumed |

```python
Trip(
    name="midday_route",
    start_time=12,
    end_time=13,
    energy_consumption=0.006,
    min_soc_at_departure=0.35,
)
```

While a trip is active, the EV cannot charge, discharge, or be assigned to a charger. Trip energy is spread evenly over the trip's timesteps and subtracted from the battery SoC. `min_soc_at_departure` guarantees the vehicle has enough charge before each trip.

Building an `ElectricVehicle` raises an `OdysValidationError` if two of its trips overlap. Creating the `EnergySystem` also checks that every trip ends within `number_of_steps`.

See the [formulation](#math-trips).

## Initial and final state

Where the vehicle's battery starts and ends belongs to the run. Pass an `ElectricVehicleInitialState` (required) and, optionally, an `ElectricVehicleFinalState` to the `EnergySystem`:

| Class                         | Field     | Type              | Description                                |
| ----------------------------- | --------- | ----------------- | ------------------------------------------ |
| `ElectricVehicleInitialState` | `vehicle` | `ElectricVehicle` | The vehicle                                |
|                               | `soc`     | `float`           | State of charge just before the first step |
| `ElectricVehicleFinalState`   | `vehicle` | `ElectricVehicle` | The vehicle                                |
|                               | `soc`     | `float`           | State of charge at the last step           |

Building the `ElectricVehicleInitialState` raises an `OdysValidationError` if a trip departing at `start_time=0` cannot be served from the starting charge. That happens when the trip needs a higher `min_soc_at_departure` than the initial `soc`, or more energy than the battery holds above `soc_min` at the start (`(soc − soc_min) × capacity`). There is no earlier step to charge in, and the vehicle cannot charge while driving.

See [Battery](battery.md#state-of-charge-soc) for how the states shape the state of charge, and the [formulation](battery.md#math-soc).

## Results

After optimization, access EV results through `result.electric_vehicles`:

```python
result = energy_system.optimize()

result.electric_vehicles.net_power  # positive = charging, negative = discharging
result.electric_vehicles.soc  # state of charge (fraction of capacity)
result.electric_vehicles.charge_mode  # binary charging mode
```

## Mathematical formulation

An electric vehicle $e$ has all the variables and constraints of the [Battery formulation](battery.md#mathematical-formulation), with $b = e$. The trip schedule adds the constraints below. Charger coupling is on the [Charger](charger.md#mathematical-formulation) page. See [Mathematical notation](../mathematical_notation.md) for every symbol.

### Variables

Those of the [Battery](battery.md#variables). Trips add no variables: $\omega_{e,t}$, $\Delta SOC^{trip}_{e,t}$ and $SOC^{dep}_{e,t}$ are parameters derived from the trip schedule.

### Constraints

#### Trips {#math-trips}

For a trip $k$ of vehicle $e$ from $t^{start}_k$ to $t^{end}_k$ consuming $E^{trip}_k$, at every step $t^{start}_k \le t < t^{end}_k$:

$$
\omega_{e,t} = 1, \qquad
\Delta SOC^{trip}_{e,t} = \frac{E^{trip}_k}{\left(t^{end}_k - t^{start}_k\right) E_e}
$$

and both are 0 outside trips. The trip energy is subtracted in the battery's SOC dynamics:

$$
SOC_{e,t,s} = SOC_{e,t-1,s} \left(1 - \delta_e \Delta t\right)
+ \eta^{ch}_e \frac{\Delta t}{E_e} p^{ch}_{e,t,s}
- \frac{\Delta t}{\eta^{dis}_e E_e} p^{dis}_{e,t,s}
- \Delta SOC^{trip}_{e,t}
$$

(and likewise at $t = 0$, starting from $SOC^{start}_e$).

#### Driving unavailability {#math-driving}

$$
p^{ch}_{e,t,s} + p^{dis}_{e,t,s} \le \left(P^{ch,\max}_e + P^{dis,\max}_e\right)\left(1 - \omega_{e,t}\right)
$$

#### Departure SoC {#math-departure}

$$
SOC_{e,t,s} \ge SOC^{dep}_{e,t+1}
$$

where $SOC^{dep}_{e,t}$ is the trip's `min_soc_at_departure` at its start step $t^{start}_k$, and 0 elsewhere. The SoC must be reached by the end of the step before departure.

### Objective contribution

The battery degradation cost; see [Battery](battery.md#math-objective).

### Power balance contribution

Discharging (V2G) is supply ($+\sum_e p^{dis}_{e,t,s}$) and charging is demand ($\sum_e p^{ch}_{e,t,s}$). See [Power balance](../concepts/power_balance.md).

## Next steps

EVs need chargers to connect to the grid. See [Charger](charger.md) for assignment and power limits, or the [EV Fleet example](../../examples/ev_fleet_optimization.md) for a full worked scenario.
