---
icon: fontawesome/solid/battery-three-quarters
---

# Battery

A `Battery` describes the physics of an energy store: how much it holds, how fast it charges and discharges, what it loses on the way, and how full it may get. Two assets have one:

- a [StationaryStorage](stationary_storage.md) is a battery at a site, such as a grid-scale BESS;
- an [ElectricVehicle](electric_vehicle.md) is a battery that drives away on trips.

Everything on this page applies to both. A `Battery` has no name and is never added to a portfolio on its own: the asset that owns it is.

## Basic usage

Let's build the battery of the [running example](../index.md#the-running-example): 50 MWh that charges and discharges at up to 25 MW, and loses 5 % each way. It sits at the site, so it goes into a `StationaryStorage`:

```python
from odys import Battery, StationaryStorage, StorageInitialState

bess = StationaryStorage(
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

The optimizer decides when the battery charges and when it discharges: it stores energy when it's cheap or would otherwise go to waste, and gives it back when it's worth more. Every battery needs an initial state, like `starts_half_full`, because its charge carries over from one step to the next (see [State of charge](#state-of-charge)).

## Fields

| Field                    | Type    | Required | Default | Description                                                      |
| ------------------------ | ------- | -------- | ------- | ---------------------------------------------------------------- |
| `capacity`               | `float` | Yes      | -       | Energy the battery holds when full, above 0 (MWh)                |
| `max_charge_power`       | `float` | Yes      | -       | Highest charging power, above 0 (MW)                             |
| `max_discharge_power`    | `float` | Yes      | -       | Highest discharging power, at least 0 (MW). `0` means charge-only |
| `efficiency_charging`    | `float` | No       | `1.0`   | Share of the charged energy that reaches the battery, above 0 and at most 1 |
| `efficiency_discharging` | `float` | No       | `1.0`   | Share of the stored energy that comes back out, above 0 and at most 1 |
| `soc_min`                | `float` | No       | `0.0`   | Lowest state of charge, as a fraction of capacity                 |
| `soc_max`                | `float` | No       | `1.0`   | Highest state of charge, as a fraction of capacity                |
| `degradation_cost`       | `float` | No       | `0.0`   | Wear cost of each MWh charged or discharged, at least 0 (currency/MWh) |
| `self_discharge_rate`    | `float` | No       | `0.0`   | Share of the stored energy lost per hour, between 0 and 1         |

## Charge and discharge limits

The battery charges at up to `max_charge_power` and discharges at up to `max_discharge_power`. At each step it does one or the other, never both. See [B-1](../../formulation/batteries.md#b-1) and [B-2](../../formulation/batteries.md#b-2).

Set `max_discharge_power=0.0` for a battery that can only charge, such as an electric vehicle without vehicle-to-grid. The opposite isn't possible: `max_charge_power` has to be above 0.

## State of charge

The state of charge is how full the battery is, as a fraction of its capacity: 0.5 is half full. odys tracks it at the end of every step, and three things shape it:

- **The initial state** sets where the battery starts. It's required, and it lies between `soc_min` and `soc_max`.
- **A final state** sets where it has to end. It's optional. Without one, the optimizer is free to empty the battery by the last step, because energy left over has no value in the run. Set one when the next run needs the battery charged.
- **`soc_min` and `soc_max`** set the range it operates in, for example to keep a margin at both ends:

```python
from odys import StorageFinalState

bounded_bess = StationaryStorage(
    name="bess",
    battery=Battery(
        capacity=50.0,
        max_charge_power=25.0,
        max_discharge_power=25.0,
        efficiency_charging=0.95,
        efficiency_discharging=0.95,
        soc_min=0.2,  # never below 20 %
        soc_max=0.9,  # never above 90 %
    ),
)
initial_conditions = (StorageInitialState(storage=bounded_bess, soc=0.5),)
final_conditions = (StorageFinalState(storage=bounded_bess, soc=0.5),)
```

Both states go to the [EnergySystem](../model/first_model.md#initial-and-final-conditions), and both have to lie within `[soc_min, soc_max]`, or creating them raises an `OdysValidationError`. A final state is an exact value: the battery ends at exactly that charge, in every scenario. An electric vehicle uses `ElectricVehicleInitialState` and `ElectricVehicleFinalState` instead, which work the same way.

See [Initial and final conditions](../concepts/initial_and_final_conditions.md#storage-and-electric-vehicles) for every field, and [B-3](../../formulation/batteries.md#b-3) to [B-5](../../formulation/batteries.md#b-5).

## Efficiency

Charging and discharging each lose energy. Charge 10 MWh at 90 % efficiency, and 9 MWh reaches the battery. Discharge those 9 MWh at 85 % efficiency, and 7.65 MWh comes back out. The round-trip efficiency is `efficiency_charging * efficiency_discharging`, here 76.5 %.

So storing only pays when the price difference covers the losses: with the running example's 95 % each way, the battery needs to sell for more than about 1.11 times what it paid. See [B-3](../../formulation/batteries.md#b-3).

## Self-discharge

`self_discharge_rate` is the share of the stored energy lost every hour, even when the battery is idle. A rate of `0.001` loses 0.1 % of the charge per hour, from the first step on. The rate is per hour, whatever the step length. See [B-3](../../formulation/batteries.md#b-3).

## Degradation cost

Every MWh through a battery wears it a little. `degradation_cost` puts a price on that wear, per MWh charged or discharged:

```python
battery = Battery(
    capacity=50.0,
    max_charge_power=25.0,
    max_discharge_power=25.0,
    efficiency_charging=0.95,
    efficiency_discharging=0.95,
    degradation_cost=5.0,  # 5 per MWh in or out
)
```

Both directions count, so storing 1 MWh and giving it back costs the wear twice. The optimizer now only cycles the battery when the price difference covers its losses and its wear. With the default of 0, cycling is free, and the battery trades on any price difference that beats its losses. See the [objective contribution](../../formulation/batteries.md#objective-contribution).

## Results

Let's add the battery to the CCGT, the wind farm and the factory, and solve. To see clearly what it does with the wind, we start it empty:

```python
from datetime import timedelta

from odys import (
    AssetPortfolio,
    AvailableCapacityProfile,
    EnergySystem,
    FixedLoad,
    Generator,
    LoadProfile,
    Scenario,
)

ccgt = Generator(name="ccgt", nominal_power=100.0, variable_cost=50.0)
wind = Generator(name="wind", nominal_power=80.0, variable_cost=0.0)
factory = FixedLoad(name="factory")

energy_system = EnergySystem(
    portfolio=AssetPortfolio([ccgt, wind, bess, factory]),
    scenarios=Scenario(
        profiles=(
            LoadProfile(load=factory, values=[60, 90, 40, 70]),
            AvailableCapacityProfile(generator=wind, values=[40, 10, 60, 30]),
        ),
    ),
    timestep=timedelta(hours=1),
    number_of_steps=4,
    initial_conditions=(StorageInitialState(storage=bess, soc=0.0),),
)

result = energy_system.optimize()
print(result.stationary_storages.to_dataframe()[["net_power", "soc"]].round(3))
```

```text
                         net_power   soc
time stationary_storage
0    bess                     0.00  0.00
1    bess                     0.00  0.00
2    bess                    20.00  0.38
3    bess                   -18.05  0.00
```

With no market to trade on, the battery stores the 20 MW of wind the factory can't use at step 2, and gives it back at step 3 in place of CCGT output. Only 95 % of the charged energy reaches the battery, and 95 % of that comes back out, so 20 MW charged raises the charge by 0.38 and returns 18.05 MW. Charging from the CCGT to discharge later would only lose energy, so the rest of the time the battery stays idle.

A battery's results are read through the asset that owns it, `result.stationary_storages` or `result.electric_vehicles`, with the same three series. Each is a `pandas.Series` indexed by asset and time, and by scenario when there's more than one:

- `net_power`: charging minus discharging, in MW, so positive while the battery charges.
- `soc`: the state of charge at the end of the step, as a fraction of capacity.
- `charge_mode`: 1 when the battery may charge, 0 when it may discharge. At a step where it's idle, either value can show up ([B-1](../../formulation/batteries.md#b-1)).

The [Battery Dispatch example](../../examples/battery_dispatch.md) stores solar for the evening over a full day.

## How it's modelled

A battery has a charging power, a discharging power and a state of charge at every step, in every scenario, plus a mode that lets it do only one of the two at a time. Stationary storages and electric vehicles share the same rules, written once on the [Batteries](../../formulation/batteries.md) formulation page, from [B-1](../../formulation/batteries.md#b-1) to [B-7](../../formulation/batteries.md#b-7). An electric vehicle adds the energy of its trips ([EV-1](../../formulation/electric_vehicles.md#ev-1)).

## Next steps

A battery needs an asset to live in. Next, see how a [StationaryStorage](stationary_storage.md) puts one at your site.
