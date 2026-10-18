---
icon: lucide/zap
---

# Your first model

Every odys model is built from two objects. An `AssetPortfolio` holds what you own and operate. An `EnergySystem` takes that portfolio and adds the rest: the markets you trade on, the futures you plan for, the horizon and where each asset starts. Calling `.optimize()` on it returns the plan.

## Basic usage

Let's build the first system of the [running example](../index.md#the-running-example): a 100 MW CCGT serving a factory over four hours.

```python
from datetime import timedelta

from odys import AssetPortfolio, EnergySystem, FixedLoad, Generator, LoadProfile, Scenario

ccgt = Generator(name="ccgt", nominal_power=100.0, variable_cost=50.0)
factory = FixedLoad(name="factory")

energy_system = EnergySystem(
    portfolio=AssetPortfolio([ccgt, factory]),
    scenarios=Scenario(profiles=(LoadProfile(load=factory, values=[60, 90, 40, 70]),)),
    timestep=timedelta(hours=1),
    number_of_steps=4,
)

result = energy_system.optimize()
print(result.generators.power)
```

```text
time  generator
0     ccgt         60.0
1     ccgt         90.0
2     ccgt         40.0
3     ccgt         70.0
Name: power, dtype: float64
```

The CCGT is the only supply, so it follows the factory's demand exactly. The optimizer maximizes profit, and here the profit is only the fuel cost: 260 MWh at 50 $/MWh is 13,000, so the objective is negative:

```python
print(result.objective_value)
```

```text
-13000.0
```

The rest of the User Guide adds to this system one piece at a time.

## The portfolio

An `AssetPortfolio` takes the assets you own and operate: [generators](../assets/generator.md), [fixed](../assets/fixed_load.md) and [flexible](../assets/flexible_load.md) loads, [stationary storage](../assets/stationary_storage.md), [electric vehicles](../assets/electric_vehicle.md) and [chargers](../assets/charger.md). Building it checks two rules, and raises an `OdysValidationError` when one fails:

- Asset names are unique within the portfolio.
- Chargers and electric vehicles come together: a portfolio with vehicles but no charger, or chargers but no vehicle, is rejected.

Markets aren't assets, so they don't go in the portfolio: pass them to the `EnergySystem` with `markets=...` (see [EnergyMarket](../markets/energy_market.md)).

When you build portfolios in a script, you can read the assets back by name or by type:

```python
portfolio = AssetPortfolio([ccgt, factory])

portfolio.get_asset("ccgt")  # the Generator named "ccgt"
portfolio.assets_of(Generator)  # (ccgt,), in the order you added them
portfolio.assets  # every asset, keyed by name, read-only
```

## EnergySystem parameters

| Parameter            | Type                                             | Required | Default       | Description                                                   |
| -------------------- | ------------------------------------------------ | -------- | ------------- | ------------------------------------------------------------- |
| `portfolio`          | `AssetPortfolio`                                 | Yes      | -             | The assets you own and operate                                |
| `scenarios`          | `Scenario` or `list[Scenario]`                   | Yes      | -             | The futures you plan for: demand, available capacity and prices |
| `timestep`           | `timedelta`                                      | Yes      | -             | Length of each step                                           |
| `number_of_steps`    | `int`                                            | Yes      | -             | How many steps the horizon has                                |
| `markets`            | `EnergyMarket` or `list[EnergyMarket]` or `None` | No       | `None`        | The markets you buy from and sell to                          |
| `objective`          | `Objective`                                      | No       | `Objective()` | What to maximize: expected profit by default                  |
| `initial_conditions` | sequence of initial states                       | No       | `()`          | Where each asset starts, just before the first step           |
| `final_conditions`   | sequence of final states                         | No       | `()`          | Where an asset has to be at the last step                     |

Each one is covered on its own page:

- **`scenarios`**: a single [Scenario](profiles.md) holds the time series of one future. A list of them plans against [several futures](../uncertainty/scenarios.md).
- **`timestep`** and **`number_of_steps`**: see [Time and units](time_and_units.md).
- **`markets`**: see [EnergyMarket](../markets/energy_market.md).
- **`objective`**: see [Objective](../optimization/objective.md), to weigh profit against risk.
- **`initial_conditions`** and **`final_conditions`**: see [below](#initial-and-final-conditions).

Creating the `EnergySystem` checks the whole configuration before anything is solved, and raises an `OdysValidationError` on the first problem. See [Validation and errors](../solving/validation.md).

## Initial and final conditions

Some assets carry state from one step to the next: a generator's output, a battery's charge. An initial condition says where such an asset starts, and a final condition where it has to end. Say you're planning tomorrow's dispatch: the CCGT running tonight and the battery's charge at midnight are where tomorrow starts.

Conditions go to the `EnergySystem`, not to a `Scenario`, because they're the same in every future: you know the starting state when you plan, and a final state is a target you choose. Each asset has at most one of each.

| Asset | Initial condition | Final condition | Initial condition required |
| ----- | ----------------- | --------------- | -------------------------- |
| [Generator](../assets/generator.md#initial-and-final-state) | `GeneratorInitialState` | `GeneratorFinalState` | When its start matters: ramp limits, minimum up or down times, start-up or shut-down costs |
| [StationaryStorage](../assets/stationary_storage.md#initial-and-final-state) | `StorageInitialState` | `StorageFinalState` | Always |
| [ElectricVehicle](../assets/electric_vehicle.md#initial-and-final-state) | `ElectricVehicleInitialState` | `ElectricVehicleFinalState` | Always |

Final conditions are always optional. Loads, chargers and markets carry no state, so they take none. Each asset page shows its conditions in code.

## Optimizing

`.optimize()` builds the model as a mixed-integer linear program and solves it with HiGHS, unless you choose another solver with a `SolverConfig` (see [Solvers](../solving/solvers.md)). It returns the results, one container per asset type; see [Results](../solving/results.md). The exact model is written out in the [Mathematical Formulation](../../formulation/index.md).

## Next steps

Every value in this model was a power, a price or a step length. Next, see how odys reads each of them, in [Time and units](time_and_units.md).
