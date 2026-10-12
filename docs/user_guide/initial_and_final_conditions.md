---
icon: lucide/flag
---

# Initial and final conditions

An optimization run rarely starts from scratch. A gas turbine that ran yesterday is still on this morning, and a battery is as full as yesterday left it. Initial conditions tell the optimizer where each asset starts; final conditions tell it where an asset must end, so the next run can pick up from there.

See [Mathematical notation](mathematical_notation.md) for the full list of symbols used below.

## Basic usage

Let's start a day with a gas turbine already running and a half-full battery, and ask for the battery to be half full again at the end.

```python
from datetime import timedelta

from odys import (
    AssetPortfolio,
    Battery,
    EnergySystem,
    FixedLoad,
    Generator,
    GeneratorInitialState,
    LoadProfile,
    Scenario,
    StationaryStorage,
    StorageFinalState,
    StorageInitialState,
)

ccgt = Generator(name="ccgt", nominal_power=100.0, min_power=30.0, variable_cost=45.0, ramp_up=40.0)
bess = StationaryStorage(name="bess", battery=Battery(capacity=50.0, max_charge_power=25.0, max_discharge_power=25.0))
load = FixedLoad(name="demand")

energy_system = EnergySystem(
    portfolio=AssetPortfolio([ccgt, bess, load]),
    scenarios=Scenario(profiles=(LoadProfile(load=load, values=[60, 90, 40, 70]),)),
    timestep=timedelta(hours=1),
    number_of_steps=4,
    initial_conditions=(
        GeneratorInitialState(generator=ccgt, power=50.0),
        StorageInitialState(storage=bess, soc=0.5),
    ),
    final_conditions=(StorageFinalState(storage=bess, soc=0.5),),
)

result = energy_system.optimize()
```

Because the CCGT starts at 50 MW with a 40 MW/h ramp limit, it can produce at most 90 MW in the first hour.

Conditions are passed to the `EnergySystem`, not to a `Scenario`. The starting state is something you know when you optimize, so it is the same in every scenario. A final condition is a target you choose, not an uncertain input.

## Condition types

Each condition holds the asset it belongs to, so it cannot be attached to the wrong kind of asset:

| Asset               | Initial condition             | Final condition             | Initial condition required                      |
| ------------------- | ----------------------------- | --------------------------- | ----------------------------------------------- |
| `Generator`         | `GeneratorInitialState`       | `GeneratorFinalState`       | When its results depend on it (see below)       |
| `StationaryStorage` | `StorageInitialState`         | `StorageFinalState`         | Always                                          |
| `ElectricVehicle`   | `ElectricVehicleInitialState` | `ElectricVehicleFinalState` | Always                                          |

Final conditions are always optional. Loads, chargers and markets carry no state from one step to the next, so they have no conditions. Each asset has at most one condition of each type.

## Generators

A generator's state is its output: 0 MW means off, any other output means on.

| Class                   | Field           | Type                | Description                                                         |
| ----------------------- | --------------- | ------------------- | ------------------------------------------------------------------- |
| `GeneratorInitialState` | `generator`     | `Generator`         | The generator                                                       |
|                         | `power`         | `float`             | Output just before the first step: 0 or within `[min_power, nominal_power]` |
|                         | `time_in_state` | `timedelta \| None` | How long it has been on (`power > 0`) or off (`power = 0`)          |
| `GeneratorFinalState`   | `generator`     | `Generator`         | The generator                                                       |
|                         | `power`         | `float`             | Output at the last step: 0 or within `[min_power, nominal_power]`   |

The initial state sets the generator's status and output just before the first step, $u^0_g$ and $p^0_g$. They feed the first step of every constraint that looks one step back:

- **Ramp limits** apply from the initial output: $p_{g,0} - p^0_g \le R^{up}_g$ and $p^0_g - p_{g,0} \le R^{down}_g$.
- **Startup and shutdown** are counted from the initial status, so a generator that is already on pays no startup cost.
- **Minimum up and down times** carry over. `time_in_state` is $T^0_g$, the steps already spent in the initial state. A generator that has been on for 1 hour with a 3-hour `min_up_time` must stay on for 2 more hours.

A `GeneratorInitialState` is required when the generator has `ramp_up`, `ramp_down`, `min_up_time`, `min_down_time`, `startup_cost` or `shutdown_cost` set. Without any of these, the starting state doesn't change the result, so you can leave it out and the generator starts off.

`time_in_state` is required when the matching minimum time is set: `min_up_time` for a generator that starts on, `min_down_time` for one that starts off. It must be a whole number of timesteps. Leave it out otherwise; the generator then counts as having been in its state long enough.

A final state fixes the output at the last step, $p_{g,T-1} = p^{end}_g$. Use `power=0.0` to have the generator off at the end of the horizon.

See [Generator](generator.md#initial-and-final-state) for the full constraints.

## Storage and electric vehicles

A battery's state is its state of charge, as a fraction of capacity:

| Class                         | Field     | Type                | Description                                 |
| ----------------------------- | --------- | ------------------- | ------------------------------------------- |
| `StorageInitialState`         | `storage` | `StationaryStorage` | The storage                                 |
|                               | `soc`     | `float`             | State of charge just before the first step  |
| `StorageFinalState`           | `storage` | `StationaryStorage` | The storage                                 |
|                               | `soc`     | `float`             | State of charge at the last step            |
| `ElectricVehicleInitialState` | `vehicle` | `ElectricVehicle`   | The vehicle                                 |
|                               | `soc`     | `float`             | State of charge just before the first step  |
| `ElectricVehicleFinalState`   | `vehicle` | `ElectricVehicle`   | The vehicle                                 |
|                               | `soc`     | `float`             | State of charge at the last step            |

Both must lie within the battery's `[soc_min, soc_max]`. The initial state of charge $SOC^{start}_b$ starts the [state of charge dynamics](storage.md#state-of-charge-soc). A final state fixes the last step, $SOC_{b,T-1} = SOC^{end}_b$.

An electric vehicle's initial state is also checked against its trips. A trip departing at the first step must fit the starting charge, because there is no earlier step to charge in. See [ElectricVehicle](electric_vehicle.md#trips).

## Rolling horizon

Conditions let you chain runs: optimize today, then start tomorrow from where today ended.

```python
today = result

tomorrow_starts_from = (
    GeneratorInitialState(generator=ccgt, power=round(today.generators["ccgt"].power.iloc[-1], 6)),
    StorageInitialState(storage=bess, soc=round(today.stationary_storages["bess"].soc.iloc[-1], 6)),
)
```

Round the solved values: the solver can return 29.9999999 MW for a generator at its 30 MW minimum, and odys checks that a condition's output is either 0 or at least `min_power`.

## Next steps

See [Optimization](optimization.md) for how to read the results of a run, or [Stochastic Optimization](stochastic.md) to optimize over several scenarios that share the same starting state.
