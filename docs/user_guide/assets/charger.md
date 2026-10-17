---
icon: fontawesome/solid/charging-station
---

# Charger

A `Charger` is charging infrastructure for [ElectricVehicle](electric_vehicle.md) assets. The optimizer decides which vehicle each charger serves at every timestep, and the charger caps the power of that connection.

Chargers do not take part in the power balance themselves: the vehicles connected to them do.

## Basic usage

Let's give the depot of the [ElectricVehicle](electric_vehicle.md) page one 22 kW charger for its two vans:

```python
from odys import Charger

charger = Charger(name="charger", max_power=0.022)  # 22 kW
```

Add chargers to the same portfolio as the EVs:

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

| Field        | Type    | Required | Default | Description                                             |
| ------------ | ------- | -------- | ------- | ------------------------------------------------------- |
| `name`       | `str`   | Yes      | -       | Unique identifier for the charger                       |
| `max_power`  | `float` | Yes      | -       | Maximum charge/discharge power through the charger (MW) |
| `efficiency` | `float` | No       | `1.0`   | Charger efficiency (0-1)                                |

!!! warning

    `efficiency` is not used by the model yet: charger losses are not modelled, whatever its value. Model losses with the battery's `efficiency_charging` and `efficiency_discharging` instead.

## Assignment rules

The optimizer decides charger-to-EV assignment at each timestep with these rules:

1. Each charger serves at most one EV at a time
2. Each EV connects to at most one charger at a time
3. An EV cannot be assigned to a charger while driving
4. Without a charger assigned, an EV cannot charge or discharge (including V2G)

That means charger capacity is a hard bottleneck. With one charger and two vans, the optimizer must decide who charges when, based on trip deadlines and price signals.

See the [formulation](#math-assignment).

## Results

Let's solve the depot of the [ElectricVehicle](electric_vehicle.md#results) page and read the chargers' results through `result.chargers`:

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

Every row has a single 1 across the assignment columns: the charger serves one van at a time. `van_2` gets it while `van_1` is on its morning trip (steps 2 and 3) and at step 5, just before its own departure. The rest of the shift it goes to `van_1`, which charges before its trip and sells energy back afterwards.

`assignment` is 1 when a vehicle is connected to a charger, indexed by time, charger and vehicle; the dataframe has one `assignment[...]` column per vehicle. `power` is the charging power drawn through each charger (MW), indexed by charger and time. It counts charging only: power a vehicle discharges through the charger (V2G) is in that vehicle's [`net_power`](electric_vehicle.md#results), not in `power`. Both are `pandas.Series`, with a scenario level when there is more than one scenario.

See the [EV Fleet example](../../examples/ev_fleet_optimization.md) for V2G arbitrage and charger competition across three vans and two chargers.

## Mathematical formulation

### Variables

| Symbol | Result attribute | Domain | Meaning |
| ------ | ---------------- | ------ | ------- |
| $a_{c,e,t,s}$ | `assignment` | $\{0,1\}$ | 1 when vehicle $e$ is connected to charger $c$ |
| $\sum_e a_{c,e,t,s} \, p^{ch}_{e,t,s}$ | `power` | - | Charging power drawn through charger $c$, without V2G discharge (reported, not a model variable) |

### Constraints

#### Assignment {#math-assignment}

$$
\sum_e a_{c,e,t,s} \le 1, \qquad
\sum_c a_{c,e,t,s} \le 1, \qquad
a_{c,e,t,s} \le 1 - \omega_{e,t}
$$

#### Power limit {#math-power-limit}

$$
p^{ch}_{e,t,s} + p^{dis}_{e,t,s} \le \sum_c P^{\max}_c \, a_{c,e,t,s}
$$

With no charger assigned, the right-hand side is 0, so the vehicle can neither charge nor discharge.

### Objective contribution

None.

### Power balance contribution

None: the vehicles connected to the chargers carry the power. See [Electric vehicles and chargers](../../formulation/electric_vehicles.md#power-balance-contribution).

## Next steps

That completes the assets. The depot above already traded with the grid; next, see [EnergyMarket](../markets/energy_market.md) for how markets work.
