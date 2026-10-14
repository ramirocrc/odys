---
icon: lucide/zap
---

# EnergySystem

`EnergySystem` is the entry point for setting up and running an optimization. You give it a portfolio of assets, the scenario data and the time configuration, then call `.optimize()`.

We designed `EnergySystem` as a single orchestrator because energy optimization involves multiple moving parts: assets, scenarios, time, and markets. Keeping them together in one object makes the workflow straightforward and validates everything at once.

See the [User Guide overview](../index.md) for how the main objects relate to each other.

## Basic usage

Let's set up our first system: the CCGT of the [running example](../index.md#the-running-example) serving a factory over four hours.

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

The CCGT is the only supply, so it follows the factory's demand exactly. The objective is the profit: 260 MWh produced at 50 $/MWh is a cost of 13,000, so the profit is negative:

```python
print(result.objective_value)
```

```text
-13000.0
```

The rest of the User Guide adds to this system one piece at a time.

## Constructor parameters

| Parameter            | Type                                             | Required | Default       | Description                                                   |
| -------------------- | ------------------------------------------------ | -------- | ------------- | ------------------------------------------------------------- |
| `portfolio`          | `AssetPortfolio`                                 | Yes      | -             | The assets you own and operate                                |
| `scenarios`          | `Scenario` or `list[Scenario]`                   | Yes      | -             | Scenario data (demand, available capacity and price profiles) |
| `timestep`           | `timedelta`                                      | Yes      | -             | Duration of each time period                                  |
| `number_of_steps`    | `int`                                            | Yes      | -             | How many timesteps to optimize over                           |
| `markets`            | `EnergyMarket` or `list[EnergyMarket]` or `None` | No       | `None`        | Energy markets for buying and selling                         |
| `objective`          | `Objective`                                      | No       | `Objective()` | What to maximize. Defaults to expected profit                 |
| `initial_conditions` | sequence of initial states                       | No       | `()`          | State of each asset just before the first step                |
| `final_conditions`   | sequence of final states                         | No       | `()`          | State each asset must reach at the last step                  |

Each parameter has its own page:

- **`portfolio`**: the assets go in an [AssetPortfolio](asset_portfolio.md).
- **`scenarios`**: a single [Scenario](scenario.md) for a deterministic run, or a list of them for [stochastic optimization](../optimization/stochastic.md).
- **`markets`**: see [EnergyMarket](../markets/energy_market.md). Markets are passed here, not in the portfolio, and their prices live in the scenarios.
- **`initial_conditions`** and **`final_conditions`**: see [Initial and final conditions](initial_and_final_conditions.md). Every storage and EV needs an initial state.
- **`objective`**: see [Objective](../optimization/objective.md) to balance profit against risk.

## Running the optimization

`.optimize()` builds and solves the model, and returns an `OptimalDispatchResults` object. It uses HiGHS unless you pass a `SolverConfig` (see [Solvers](../optimization/solvers.md)). See [Results](../optimization/results.md) for how to read the results.

## Validation

Creating an `EnergySystem` validates the whole configuration and raises an `OdysValidationError` on the first problem it finds. Checks that concern a single object, such as overlapping EV trips or an available capacity above a generator's nominal power, already ran when that object was built, and a non-positive `timestep` or fewer than one step is a field error (see [Errors](#errors)). The system-level checks are:

- scenario probabilities sum to 1 and scenario names are unique
- every initial and final condition references an asset of the portfolio, with at most one condition of each type per asset
- every storage and EV has an initial state, and so does every generator with ramp limits, minimum up or down times, or startup or shutdown costs
- minimum up and down times and each generator's `time_in_state` are a whole number of timesteps, and each generator's final power fits its available capacity at the last step
- every profile references an asset of the portfolio or one of the markets
- every load has a `LoadProfile`, and every market a `PriceProfile`, in every scenario
- every profile has `number_of_steps` values, and every EV trip starts and ends on a timestep and within the horizon
- in every scenario and at every timestep, the maximum supply (generators, storage and EV discharge, market volume) covers the minimum demand (fixed loads, plus flexible loads after their maximum decrease)
- without markets, the energy available over the horizon covers the minimum energy demand

For example, a profile one value short is caught when the system is created, before anything is solved:

```python
from odys import OdysValidationError

try:
    EnergySystem(
        portfolio=AssetPortfolio([ccgt, factory]),
        scenarios=Scenario(profiles=(LoadProfile(load=factory, values=[60, 90, 40]),)),
        timestep=timedelta(hours=1),
        number_of_steps=4,
    )
except OdysValidationError as error:
    print(error)
```

```text
Scenario 'base': the LoadProfile for 'factory' has 3 values, but the horizon has 4 steps.
```

## Errors

Odys's own errors derive from `OdysError` and are exported from `odys`, so `except odys.OdysValidationError` works:

| Exception                  | Raised when                                                                                         |
| -------------------------- | --------------------------------------------------------------------------------------------------- |
| `OdysValidationError`      | An input breaks a rule of Odys: when an asset, profile, condition or the `EnergySystem` is built     |
| `OdysSolverError`          | The requested solver is not installed, or you read results of a run that found no solution          |
| `OdysNoResultsError`       | You read a results container the system does not have, such as `result.markets` without markets     |
| `pydantic.ValidationError` | A single field is out of range or of the wrong type, such as a negative `capacity`                  |

Field types and ranges are checked by pydantic, the library Odys's inputs are built on, so they raise its `ValidationError`, which names the field.

## What happens under the hood

When you call `.optimize()`, Odys:

1. Builds a mixed-integer linear program (MILP) using linopy from the validated configuration
2. Solves it with the HiGHS solver (or the solver you configure)
3. Wraps the solution in an `OptimalDispatchResults` object

You don't need to interact with any of these internals, but if you're curious, the [Developer Reference](../../developer/index.md) has the full details.

## Next steps

Next, let's look at the [AssetPortfolio](asset_portfolio.md) that holds the assets.
