---
icon: fontawesome/solid/charging-station
---

# Charger

A `Charger` models a charging point: the plug that connects an [ElectricVehicle](electric_vehicle.md) to the grid. At every step, the optimizer decides which vehicle each charger serves, and the charger's rating caps how fast that vehicle charges or, with V2G, discharges.

Chargers and vehicles come together: a portfolio with electric vehicles needs at least one charger, and a portfolio with chargers needs at least one vehicle. Building the `AssetPortfolio` raises an `OdysValidationError` otherwise.

## Basic usage

Let's give the depot of the [ElectricVehicle](electric_vehicle.md) page one 22 kW charger for its two vans:

```python
from odys import Charger

charger = Charger(name="charger", max_power=0.022)  # 22 kW
```

The charger goes into the same portfolio as the vans:

```python
from datetime import timedelta

from odys import AssetPortfolio, Battery, ElectricVehicle, Trip

van_1 = ElectricVehicle(
    name="van_1",
    battery=Battery(
        capacity=0.100,
        max_charge_power=0.022,
        max_discharge_power=0.011,
        efficiency_charging=0.95,
        efficiency_discharging=0.95,
    ),
    trips=(
        Trip(
            name="morning_delivery",
            start_time=timedelta(hours=2),
            end_time=timedelta(hours=4),
            energy_consumption=0.030,
            min_soc_at_departure=0.8,
        ),
    ),
)
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

portfolio = AssetPortfolio([van_1, van_2, charger])
```

## Fields

| Field        | Type    | Required | Default | Description                                                     |
| ------------ | ------- | -------- | ------- | --------------------------------------------------------------- |
| `name`       | `str`   | Yes      | -       | Unique name of the charger                                      |
| `max_power`  | `float` | Yes      | -       | Highest power through the charger, charging or discharging, above 0 (MW) |
| `efficiency` | `float` | No       | `1.0`   | Not used by the model yet; see below                            |

`efficiency` has no effect today: charging through a charger loses nothing beyond the battery's own efficiencies. Put the charger's losses into the battery's `efficiency_charging` and `efficiency_discharging` instead. See [CH-4](../../formulation/electric_vehicles.md#ch-4).

## Sharing chargers

With fewer chargers than vehicles, the chargers are the bottleneck, and the optimizer decides who charges when, from the trips and the prices. At every step:

- a charger serves at most one vehicle, and a vehicle uses at most one charger;
- a vehicle on a trip isn't connected to any charger;
- a vehicle without a charger can't charge or discharge;
- a connected vehicle charges or discharges at most at the charger's `max_power`, and at most at its own battery's ratings.

A vehicle can move to another charger from one step to the next, at no cost, and any charger lets a vehicle with V2G discharge. See [CH-1](../../formulation/electric_vehicles.md#ch-1) to [CH-4](../../formulation/electric_vehicles.md#ch-4).

## Results

The depot is complete now. Let's connect it to the grid, with a price that changes through the shift (see [EnergyMarket](../markets/energy_market.md)), and solve it. First, the vans' state of charge, through `result.electric_vehicles`:

```python
from odys import (
    ElectricVehicleFinalState,
    ElectricVehicleInitialState,
    EnergyMarket,
    EnergySystem,
    PriceProfile,
    Scenario,
)

grid = EnergyMarket(name="grid", max_trading_volume_per_step=1.0)

energy_system = EnergySystem(
    portfolio=portfolio,
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

The trips shape the vans' day:

- `van_1` charges in the first two hours and leaves at step 2 with 92 %, above the required 80 %, because it can sell the extra back at 80 $/MWh when it returns at step 4.
- Each trip lowers the state of charge evenly over its steps: 0.15 per step for `van_1`'s 30 kWh over two steps.
- After charging again at steps 6 and 7, `van_1` discharges at 11 kW (V2G) through the afternoon price peak, down to the required 50 %.

Now the charger, through `result.chargers`:

```python
print(result.chargers.to_dataframe().round(3))
```

```text
              assignment[van_1]  assignment[van_2]  power
time charger
0    charger                1.0                0.0  0.022
1    charger                1.0                0.0  0.022
2    charger                0.0                1.0  0.022
3    charger                0.0                1.0  0.000
4    charger                1.0                0.0  0.000
5    charger                0.0                1.0  0.022
6    charger                1.0                0.0  0.022
7    charger                1.0                0.0  0.022
8    charger                1.0                0.0  0.000
9    charger                1.0                0.0  0.000
10   charger                1.0                0.0  0.000
11   charger                1.0                0.0  0.000
```

Every row has a single 1: the charger serves one van at a time. `van_2` gets it while `van_1` is on its morning trip, at steps 2 and 3, and at step 5, just before its own route. The rest of the shift it goes to `van_1`.

`result.chargers` has two series, with a scenario level when there's more than one scenario:

- `assignment`: 1 when a vehicle is connected to a charger, indexed by time, charger and vehicle. The dataframe has one `assignment[...]` column per vehicle.
- `power`: the charging power drawn through each charger, in MW. It counts charging only: what a vehicle discharges through the charger (V2G) is in that vehicle's `net_power`, not here. That's why `power` is 0 at steps 3, 4 and 8 to 11: the connected van feeds power back then, as its falling state of charge shows.

The [EV Fleet example](../../examples/ev_fleet_optimization.md) runs three vans and two chargers over a full day.

## How it's modelled

A charger adds one decision per vehicle and step: whether that vehicle is connected to it. [CH-1](../../formulation/electric_vehicles.md#ch-1) to [CH-3](../../formulation/electric_vehicles.md#ch-3) decide who may connect, and [CH-4](../../formulation/electric_vehicles.md#ch-4) caps the vehicle's power at the rating of its charger, or 0 without one. A charger has no term of its own in the power balance or the objective. The rules and their limitations are on the [Electric vehicles and chargers](../../formulation/electric_vehicles.md) formulation page.

## Next steps

The depot traded with the grid through a market. Next, see how an [EnergyMarket](../markets/energy_market.md) works.
