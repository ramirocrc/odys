---
icon: fontawesome/solid/car-battery
---

# StationaryStorage

A `StationaryStorage` models a stationary energy storage system in your portfolio, such as a grid-scale battery. The optimizer decides when to charge and discharge it to maximize profit: it stores energy when it is cheap or would otherwise be wasted, and releases it when it is valuable.

A storage asset *has* a [Battery](battery.md): the asset is the site you own, and the battery describes its physics (capacity, power limits, efficiencies, state of charge limits).

## Basic usage

Let's add the battery of the [running example](../index.md#the-running-example) to the site: 50 MWh that charges and discharges at up to 25 MW.

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

Pass `starts_half_full` to the energy system with `EnergySystem(..., initial_conditions=(starts_half_full,))`. Every storage needs an initial state: its state of charge carries over from one step to the next, so Odys never guesses where it starts.

## Fields

| Field     | Type      | Required | Default | Description                                             |
| --------- | --------- | -------- | ------- | ------------------------------------------------------- |
| `name`    | `str`     | Yes      | -       | Unique identifier for the storage                       |
| `battery` | `Battery` | Yes      | -       | The battery's physics; see [Battery](battery.md#fields) |

Capacity, power limits, efficiencies, SOC limits, self-discharge and degradation cost are all set on the `Battery`, and the [Battery](battery.md) page explains each of them.

## Initial and final state

Where the storage starts and ends belongs to the run, not to the battery. Pass a `StorageInitialState` (required) and, optionally, a `StorageFinalState` to the `EnergySystem`. Both take the storage and a `soc`, the state of charge as a fraction of capacity.

A final state is useful when the next run needs the battery charged: without one, the optimizer is free to empty it by the end of the horizon.

See [Initial and final conditions](../concepts/initial_and_final_conditions.md#storage-and-electric-vehicles) for every field, and the [formulation](battery.md#math-soc).

## Results

Let's add the battery to the CCGT, the wind farm and the factory, and read its results through `result.stationary_storages`. To see clearly what it does with the wind, we start it empty:

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

`net_power` is in MW, positive when charging and negative when discharging. `soc` is the state of charge at the end of each step, as a fraction of capacity, and `charge_mode` is 1 when the battery may charge. Each is a `pandas.Series` indexed by storage and time (and scenario, when there is more than one).

Notice what the battery does with no market to trade in: it stores the 20 MW of wind the factory can't use at step 2 and returns it at step 3, replacing CCGT output. Only 95% of each charged MWh reaches the battery and 95% of each stored MWh comes back out, so 20 MW charged raises the SOC by 0.38 and returns 18.05 MW. Charging from the CCGT to discharge later would only lose energy, so the battery stays idle the rest of the time.

See the [Battery Dispatch example](../../examples/battery_dispatch.md) for a full day of storing solar for the evening.

## Mathematical formulation

A stationary storage is a [Battery](battery.md#mathematical-formulation) at a fixed site, with $b$ ranging over the stationary storages.

### Variables

Those of the [Battery](battery.md#variables): $p^{ch}_{b,t,s}$, $p^{dis}_{b,t,s}$, $p^{net}_{b,t,s}$, $SOC_{b,t,s}$ and $z_{b,t,s}$.

### Constraints

Those of the [Battery](battery.md#constraints): [charge and discharge limits](battery.md#math-power-limits), [state of charge](battery.md#math-soc) and [net power](battery.md#math-net-power). A stationary storage adds none of its own.

### Objective contribution

The battery's degradation cost; see [Battery](battery.md#math-objective).

### Power balance contribution

Discharging is supply ($+\sum_b p^{dis}_{b,t,s}$) and charging is demand ($\sum_b p^{ch}_{b,t,s}$). See [Power balance](../concepts/power_balance.md).

## Next steps

Next, see [Battery](battery.md) for the physics behind every storage: efficiencies, SOC limits, self-discharge and degradation.
