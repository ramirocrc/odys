---
icon: fontawesome/solid/car
---

# ElectricVehicle

An `ElectricVehicle` is an electric vehicle: it has a [Battery](battery.md) and a trip schedule. Trips make the vehicle unavailable for charging while driving and consume energy from the battery.

The optimizer decides when each vehicle charges, and when it discharges back to the grid (V2G), so that every trip departs with enough charge at the lowest cost. Unlike a [StationaryStorage](stationary_storage.md), an EV must connect through a [Charger](charger.md) to charge or discharge. With more EVs than chargers, the optimizer assigns vehicles to chargers dynamically.

EVs are a much smaller scale than the site of the [running example](../index.md#the-running-example), so this page and the [Charger](charger.md) page use a depot of two delivery vans over a 12-hour day shift in hourly steps, from 06:00. Powers and energies are still in MW and MWh, so a 22 kW charger is `0.022`.

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

The van starts the shift half charged, must leave at 08:00 with at least 80%, and must be back at 50% at the end of the shift. Pass the states to the `EnergySystem` (`initial_conditions=...`, `final_conditions=...`); see [Initial and final state](#initial-and-final-state).

## Fields

| Field     | Type               | Required | Default | Description                                              |
| --------- | ------------------ | -------- | ------- | -------------------------------------------------------- |
| `name`    | `str`              | Yes      | -       | Unique identifier for the EV                             |
| `battery` | `Battery`          | Yes      | -       | The vehicle's battery; see [Battery](battery.md#fields)  |
| `trips`   | `tuple[Trip, ...]` | Yes      | -       | Trip schedule. Can be empty if the EV stays at the depot |

## Vehicle-to-grid (V2G)

The battery's `max_discharge_power` is what enables V2G. With `max_discharge_power=0`, the vehicle can only charge. Like charging, discharging only happens through a [Charger](charger.md).

See the [formulation](../../formulation/batteries.md#b-1).

## Trips

A `Trip` defines when the vehicle is driving, how much energy it consumes, and the minimum state of charge required at departure:

| Field                  | Type    | Required | Default | Description                                                                 |
| ---------------------- | ------- | -------- | ------- | --------------------------------------------------------------------------- |
| `name`                 | `str`   | Yes      | -       | Unique trip name within the vehicle                                         |
| `start_time`           | `timedelta` | Yes  | -       | Time from the start of the horizon at which the vehicle leaves              |
| `end_time`             | `timedelta` | Yes  | -       | Time from the start of the horizon at which it is back (`end_time > start_time`) |
| `energy_consumption`   | `float` | Yes      | -       | Battery-side energy consumed during the trip (MWh)                          |
| `min_soc_at_departure` | `float` | No       | `0.0`   | Minimum state of charge required at departure, before trip energy is consumed |

Trip times are measured from the start of the horizon and must fall on a timestep. The vehicle is away for every step from `start_time` until `end_time`, and back at the depot for the step that starts at `end_time`. With the horizon starting at 06:00, a second van's afternoon route from 12:00 to 15:00 starts 6 hours in and ends 9 hours in:

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

While a trip is active, the EV cannot charge, discharge, or be assigned to a charger. Trip energy is spread evenly over the trip's timesteps and subtracted from the battery's state of charge. `min_soc_at_departure` guarantees the vehicle has enough charge before each trip.

Building an `ElectricVehicle` raises an `OdysValidationError` if two of its trips overlap. Creating the `EnergySystem` also checks that every trip starts and ends on a timestep and ends within the horizon. With 15-minute steps, a trip can leave at `timedelta(minutes=45)` but not at `timedelta(minutes=50)`.

See the [formulation](#math-trips).

## Initial and final state

Where the vehicle's battery starts and ends belongs to the run. Pass an `ElectricVehicleInitialState` (required) and, optionally, an `ElectricVehicleFinalState` to the `EnergySystem`. Both take the vehicle and a `soc`, as a fraction of capacity.

Building the `ElectricVehicleInitialState` raises an `OdysValidationError` if a trip departing at the start of the horizon (`start_time=timedelta(0)`) cannot be served from the starting charge. That happens when the trip needs a higher `min_soc_at_departure` than the initial `soc`, or more energy than the battery holds above `soc_min` at the start (`(soc − soc_min) × capacity`). There is no earlier step to charge in, and the vehicle cannot charge while driving.

See [Initial and final conditions](../concepts/initial_and_final_conditions.md#storage-and-electric-vehicles) for every field, and the [formulation](../../formulation/batteries.md#b-3).

## Results

Let's put both vans in a depot with one 22 kW [Charger](charger.md) and a grid connection whose price changes through the day (see [EnergyMarket](../markets/energy_market.md)), and read their results through `result.electric_vehicles`:

```python
from datetime import timedelta

from odys import AssetPortfolio, Charger, EnergyMarket, EnergySystem, PriceProfile, Scenario

charger = Charger(name="charger", max_power=0.022)
grid = EnergyMarket(name="grid", max_trading_volume_per_step=1.0)

energy_system = EnergySystem(
    portfolio=AssetPortfolio([van_1, van_2, charger]),
    markets=grid,
    scenarios=Scenario(
        profiles=(PriceProfile(market=grid, values=[60, 45, 70, 90, 80, 55, 50, 60, 85, 120, 110, 90]),),
    ),
    timestep=timedelta(hours=1),
    number_of_steps=12,
    initial_conditions=(
        ElectricVehicleInitialState(vehicle=van_1, soc=0.5),
        ElectricVehicleInitialState(vehicle=van_2, soc=0.5),
    ),
    final_conditions=(
        ElectricVehicleFinalState(vehicle=van_1, soc=0.5),
        ElectricVehicleFinalState(vehicle=van_2, soc=0.5),
    ),
)

result = energy_system.optimize()
print(result.electric_vehicles.soc.unstack().round(2))
```

```text
ev    van_1  van_2
time
0      0.71   0.50
1      0.92   0.50
2      0.77   0.71
3      0.62   0.69
4      0.55   0.69
5      0.55   0.90
6      0.75   0.77
7      0.96   0.63
8      0.85   0.50
9      0.73   0.50
10     0.62   0.50
11     0.50   0.50
```

`net_power` is in MW, positive when charging and negative when discharging. `soc` is the state of charge at the end of each step, as a fraction of capacity, and `charge_mode` is 1 when the battery may charge. Each is a `pandas.Series` indexed by vehicle and time (and scenario, when there is more than one).

Notice how the trips shape the day:

- `van_1` charges in the first two hours and leaves at step 2 with 92%, above the required 80%, because it can sell the extra back at 80 $/MWh when it returns at step 4.
- The vans share one charger: `van_2` uses it at steps 2 and 3, while `van_1` is away, and again at step 5, just before its own route.
- Each trip lowers the state of charge evenly over its steps: 0.15 per step for `van_1`'s 30 kWh over two steps.
- After charging again at steps 6 and 7, `van_1` discharges at 11 kW (V2G) through the afternoon price peak, down to the required 50%.

See the [EV Fleet example](../../examples/ev_fleet_optimization.md) for three vans, two chargers and a full day of trips.

## Mathematical formulation

An electric vehicle $e$ has all the variables and constraints of the [Battery formulation](../../formulation/batteries.md), with $b = e$. The trip schedule adds the constraints below. Charger coupling is on the [Charger](charger.md#mathematical-formulation) page.

### Variables

Those of the [Battery](../../formulation/batteries.md#variables). Trips add no variables: $\omega_{e,t}$, $\Delta SOC^{trip}_{e,t}$ and $SOC^{dep}_{e,t}$ are parameters derived from the trip schedule.

### Constraints

#### Trips {#math-trips}

For a trip $k$ of vehicle $e$ consuming $E^{trip}_k$, $t^{start}_k$ and $t^{end}_k$ are its `start_time` and `end_time` divided by the timestep, so they count steps. At every step $t^{start}_k \le t < t^{end}_k$:

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

The battery degradation cost; see [Battery](../../formulation/batteries.md#objective-contribution).

### Power balance contribution

Discharging (V2G) is supply ($+\sum_e p^{dis}_{e,t,s}$) and charging is demand ($\sum_e p^{ch}_{e,t,s}$). See [Power balance](../concepts/power_balance.md).

## Next steps

EVs need chargers to connect to the grid. Next, see [Charger](charger.md) for how vehicles share them.
