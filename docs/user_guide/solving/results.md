---
icon: lucide/table
---

# Results

`.optimize()` returns an `OptimalDispatchResults`: one container per asset type and for the markets, with every decision as a `pandas.Series`, plus the objective value and the solver's status.

## Basic usage

Let's solve the complete [running example](../index.md#the-running-example), the site the [EnergyMarket](../markets/energy_market.md#results) page put together:

??? example "The running example"

    ```python
    from datetime import timedelta

    from odys import (
        AssetPortfolio,
        AvailableCapacityProfile,
        Battery,
        EnergyMarket,
        EnergySystem,
        FixedLoad,
        FlexibleLoad,
        Generator,
        LoadProfile,
        PriceProfile,
        Scenario,
        StationaryStorage,
        StorageInitialState,
    )

    ccgt = Generator(name="ccgt", nominal_power=100.0, variable_cost=50.0)
    wind = Generator(name="wind", nominal_power=80.0, variable_cost=0.0)
    factory = FixedLoad(name="factory")
    process = FlexibleLoad(name="process", max_increase=20.0, max_decrease=10.0, value_of_consumption=60.0)
    bess = StationaryStorage(
        name="bess",
        battery=Battery(
            capacity=50.0,
            max_charge_power=25.0,
            max_discharge_power=25.0,
            efficiency_charging=0.95,
            efficiency_discharging=0.95,
        ),
    )
    day_ahead = EnergyMarket(name="day_ahead", max_trading_volume_per_step=150.0)

    energy_system = EnergySystem(
        portfolio=AssetPortfolio([ccgt, wind, bess, factory, process]),
        markets=day_ahead,
        scenarios=Scenario(
            profiles=(
                LoadProfile(load=factory, values=[60, 90, 40, 70]),
                LoadProfile(load=process, values=[30, 30, 30, 30]),
                AvailableCapacityProfile(generator=wind, values=[40, 10, 60, 30]),
                PriceProfile(market=day_ahead, values=[40, 75, 30, 65]),
            ),
        ),
        timestep=timedelta(hours=1),
        number_of_steps=4,
        initial_conditions=(StorageInitialState(storage=bess, soc=0.5),),
    )
    ```

```python
result = energy_system.optimize()
print(result.generators.to_dataframe().round(2))
```

```text
                power  status  startup  shutdown
time generator
0    ccgt         0.0     0.0      0.0       0.0
     wind        40.0     1.0      1.0       0.0
1    ccgt       100.0     1.0      1.0       0.0
     wind        10.0     1.0      0.0       0.0
2    ccgt         0.0     0.0      0.0       1.0
     wind        60.0     1.0      0.0       0.0
3    ccgt       100.0     1.0      1.0       0.0
     wind        30.0     1.0      0.0       0.0
```

The CCGT only runs when the market price is above its 50 $/MWh cost, and the wind farm always produces what it can.

!!! note

    Solvers work in floating point, so a value that is exactly zero in theory can print as `-0.0` or as a tiny number such as `1e-12`. Round before comparing or displaying, as this page does with `.round(2)`.

## Results containers

Each asset type and the markets have their own container. What each series means is on the linked page:

| Container                    | Series                                     | Details                                                       |
| ---------------------------- | ------------------------------------------ | ------------------------------------------------------------- |
| `result.generators`          | `power`, `status`, `startup`, `shutdown`   | [Generator](../assets/generator.md#results)                   |
| `result.flexible_loads`      | `load_adjustment`, `actual_load`           | [FlexibleLoad](../assets/flexible_load.md#results)            |
| `result.stationary_storages` | `net_power`, `soc`, `charge_mode`          | [Battery](../assets/battery.md#results)                       |
| `result.electric_vehicles`   | `net_power`, `soc`, `charge_mode`          | [Battery](../assets/battery.md#results)                       |
| `result.chargers`            | `assignment`, `power`                      | [Charger](../assets/charger.md#results)                       |
| `result.markets`             | `sell_volume`, `buy_volume`, `net_volume`  | [EnergyMarket](../markets/energy_market.md#results)           |

Fixed loads have no decisions, so they have no container. Reading a container your system has no assets for, such as `result.chargers` here, raises an `OdysNoResultsError`.

## One asset at a time

A container holds every asset of its type. Select one by name, check whether one exists, or loop over them:

```python
print(result.generators["ccgt"].power.round(2))

"wind" in result.generators  # True
len(result.generators)  # 2

for generator in result.generators:
    print(round(generator.power.sum(), 2))
```

```text
time
0      0.0
1    100.0
2      0.0
3    100.0
Name: power, dtype: float64
200.0
140.0
```

Selecting one asset drops the asset level, so its series is indexed by time only, and by scenario when there's more than one.

## Data formats

Every series is a `pandas.Series`, indexed by time and asset, and by scenario when there's more than one. Each container also has `.to_dataframe()`, with one column per series, and `.to_dataset()`, an `xarray.Dataset`. A charger's `assignment` has one value per vehicle, so its dataframe has one `assignment[...]` column per vehicle:

```python
result.stationary_storages.to_dataframe()
result.markets.to_dataset()
```

For the full raw solution, with every model variable, as an `xarray.Dataset`:

```python
result.to_dataset()
```

!!! tip

    In a notebook, `result.generators.to_dataframe()` is usually the quickest way to see what the optimizer did. Export it with `.to_csv()`, or plot it directly.

## What the objective adds up

`result.objective_value` is what the optimizer maximized. By default, that's the profit, and in each scenario the profit adds up:

- the [market revenue](../../formulation/markets.md#objective-contribution): what you sell, minus what you buy, at each step's price;
- minus the [generation costs](../../formulation/generators.md#objective-contribution): variable costs, plus start-up and shut-down costs;
- plus the [value of flexible consumption](../../formulation/flexible_loads.md#objective-contribution): what each MWh a flexible load moves up is worth, minus what each MWh it gives up was worth;
- minus the [battery wear](../../formulation/batteries.md#objective-contribution), from `degradation_cost`.

```python
print(round(result.objective_value, 2))
```

```text
-7313.43
```

Here the CCGT burns 10,000 of fuel. Trading earns back about 1,487 net, and the process's 20 MWh of net extra consumption is worth 1,200 at 60 $/MWh, so the profit is −7,313. Fixed loads add nothing: serving them costs whatever the energy that covers them costs.

With several scenarios, `objective_value` is the expected profit, weighted by the scenarios' probabilities. With a CVaR term, it's the weighted sum of the expected profit and the CVaR, not a profit you can book; see [Objective](../optimization/objective.md).

## Clock time

The horizon has no start date, so the time labels count steps from `"0"` (see [Time and units](../model/time_and_units.md#the-horizon)). To show a series against clock time, map each step to its start:

```python
from datetime import datetime

start = datetime(2026, 10, 19)  # midnight, the start of the run
timestep = timedelta(hours=1)

power = result.generators.power.round(2)
print(power.rename(lambda step: start + int(step) * timestep, level="time").unstack())
```

```text
generator             ccgt  wind
time
2026-10-19 00:00:00    0.0  40.0
2026-10-19 01:00:00  100.0  10.0
2026-10-19 02:00:00    0.0  60.0
2026-10-19 03:00:00  100.0  30.0
```

## Chaining runs

A rolling horizon chains runs: you optimize today, then start tomorrow from where today ended. Read each asset's last step, and pass it as tomorrow's initial state:

```python
from odys import GeneratorInitialState

tomorrow_starts_from = (
    GeneratorInitialState(generator=ccgt, power=round(result.generators["ccgt"].power.iloc[-1], 6)),
    StorageInitialState(storage=bess, soc=round(result.stationary_storages["bess"].soc.iloc[-1], 6)),
)
```

Round the solved values. The solver can return 29.9999999 MW for a generator at its 30 MW minimum, and a generator's initial `power` has to be either 0 or at least `min_power`.

A generator with a minimum up or down time also needs its `time_in_state`: count back through its `status` from the last step to see how long it has been on or off. With several scenarios, the last step can differ between them, so pick the scenario you'll actually follow, for example `result.generators["ccgt"].power.xs("high_wind", level="scenario").iloc[-1]`.

## Solver status

```python
result.solver_status  # SolveStatus.OK ("ok") when the solver finished normally
result.termination_condition  # "optimal" when the solution is proven optimal
```

`solver_status` is one of `ok`, `warning`, `error`, `aborted` or `unknown`. `termination_condition` says why the solver stopped, for example `"optimal"`, `"infeasible"` or `"time_limit"`. A solve that hits its time limit can still return a feasible solution that isn't proven optimal.

When the run found no solution, for example because the problem is infeasible, reading any result raises an `OdysSolverError` naming the termination condition. Catch it where a run may fail:

```python
from odys import OdysSolverError

try:
    result.generators.power
except OdysSolverError as error:
    print(f"No solution: {error}")
```

## Next steps

Every run so far used HiGHS with its default settings. Next, see how to choose and tune the [Solvers](../optimization/solvers.md) behind `.optimize()`.
