---
icon: lucide/table
---

# Results

`energy_system.optimize()` returns an `OptimalDispatchResults` object with the solver status and one results container per asset type.

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

## Solver status

```python
result.solver_status  # SolveStatus.OK ("ok") when the solver finished normally
result.termination_condition  # "optimal" when the solution is proven optimal
result.objective_value  # value of the objective; see Objective
```

`solver_status` is one of `ok`, `warning`, `error`, `aborted` or `unknown`. `termination_condition` says why the solver stopped, for example `"optimal"`, `"infeasible"` or `"time_limit"`. A solve that hits its time limit can still return a feasible, not proven optimal, solution.

When the run found no solution, for example because the problem is infeasible, reading any result raises an `OdysSolverError` naming the termination condition. Catch it where a run may fail:

```python
from odys import OdysSolverError

try:
    result.generators.power
except OdysSolverError as error:
    print(f"No solution: {error}")
```

`objective_value` is the value of the whole objective: the expected profit, or the weighted profit and CVaR when the objective has a CVaR term. See [Objective](objective.md).

## Results containers

Each asset type and the markets have their own container. Its attributes are listed on the linked page:

| Container                    | Attributes                                 | Details                                                       |
| ---------------------------- | ------------------------------------------ | ------------------------------------------------------------- |
| `result.generators`          | `power`, `status`, `startup`, `shutdown`   | [Generator](../assets/generator.md#results)                   |
| `result.flexible_loads`      | `load_adjustment`, `actual_load`           | [FlexibleLoad](../assets/flexible_load.md#results)            |
| `result.stationary_storages` | `net_power`, `soc`, `charge_mode`          | [StationaryStorage](../assets/stationary_storage.md#results)  |
| `result.electric_vehicles`   | `net_power`, `soc`, `charge_mode`          | [ElectricVehicle](../assets/electric_vehicle.md#results)      |
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

Selecting one asset drops the asset level, so its series is indexed by time only (and scenario, when there is more than one).

## Rolling horizon

Conditions let you chain runs: optimize today, then start tomorrow from where today ended.

```python
from odys import GeneratorInitialState

today = result

tomorrow_starts_from = (
    GeneratorInitialState(generator=ccgt, power=round(today.generators["ccgt"].power.iloc[-1], 6)),
    StorageInitialState(storage=bess, soc=round(today.stationary_storages["bess"].soc.iloc[-1], 6)),
)
```

Round the solved values: the solver can return 29.9999999 MW for a generator at its 30 MW minimum, and Odys checks that a condition's output is either 0 or at least `min_power`.

This works for a single scenario. With several scenarios, each series has a scenario level and the last step can differ between scenarios, so pick the scenario you will actually follow, for example `today.generators["ccgt"].power.xs("high_wind", level="scenario").iloc[-1]`.

## Data formats

All of these attributes are `pandas.Series` objects, indexed by time and asset (and scenario, when there is more than one). Each container also exposes `.to_dataframe()`, with one column per attribute, and `.to_dataset()`, an `xarray.Dataset`. A charger's `assignment` has one value per vehicle, so its dataframe has one `assignment[...]` column per vehicle:

```python
result.stationary_storages.to_dataframe()
result.markets.to_dataset()
```

For the full raw solution, with every model variable, as an xarray Dataset:

```python
result.to_dataset()
```

!!! tip

    If you're working in a notebook, `result.generators.to_dataframe()` is usually the quickest way to see what the optimizer did. You can export it with `.to_csv()` or plot it directly.

## Next steps

So far every system had a single, known future. Next, see [Stochastic optimization](stochastic.md) to decide under uncertainty.
