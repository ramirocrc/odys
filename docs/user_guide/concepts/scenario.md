---
icon: lucide/file-text
---

# Scenarios and profiles

A `Scenario` describes the operating conditions of your energy system over time: how much each load demands, how much each generator can produce, and what each market pays. Each time series is a **profile** that points at the asset or market it belongs to.

## Basic usage

Let's describe the factory's demand over four timesteps.

```python
from odys import FixedLoad, LoadProfile, Scenario

factory = FixedLoad(name="factory")

scenario = Scenario(
    profiles=(LoadProfile(load=factory, values=[60, 90, 40, 70]),),
)
```

This tells the optimizer: "here's what `factory` consumes over four timesteps." The profile holds the load object itself, so it cannot be attached to the wrong kind of asset, and a typo in a name string is not possible.

We keep time series in scenarios rather than on the assets because they are what changes from one possible future to the next, while an asset's physics stay the same.

## Fields

| Field         | Type                | Required | Default  | Description                                      |
| ------------- | ------------------- | -------- | -------- | ------------------------------------------------ |
| `name`        | `str`               | No       | `"base"` | Unique identifier of the scenario                |
| `probability` | `float`             | No       | `1.0`    | Probability (0-1) of the scenario                |
| `profiles`    | `tuple` of profiles | No       | `()`     | Time series of the scenario's assets and markets |

Every profile has one value per optimization timestep, so its length must equal `number_of_steps`. Each asset or market has at most one profile of each kind per scenario.

## Profiles

| Profile                    | References   | Unit         | Required in every scenario | Meaning                                                                                                                              |
| -------------------------- | ------------ | ------------ | -------------------------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| `LoadProfile`              | `load=`      | MW           | Yes, for every load        | Demand of a [FixedLoad](../assets/fixed_load.md#profiles), or base profile of a [FlexibleLoad](../assets/flexible_load.md#profiles) |
| `AvailableCapacityProfile` | `generator=` | MW           | No                         | Upper bound on a [Generator](../assets/generator.md#profiles)'s output at each timestep                                             |
| `PriceProfile`             | `market=`    | currency/MWh | Yes, for every market      | Price of an [EnergyMarket](../markets/energy_market.md#profiles) at each timestep                                                   |

The linked **Profiles** section of each page shows an example and the validation rules for its profile. Storage, electric vehicles and chargers take no profile.

## Putting it all together

Let's add a wind farm to [our system](../model/first_model.md#basic-usage). Its output depends on the weather, so its `AvailableCapacityProfile` caps what it can produce at each step:

```python
from datetime import timedelta

from odys import AssetPortfolio, AvailableCapacityProfile, EnergySystem, Generator

ccgt = Generator(name="ccgt", nominal_power=100.0, variable_cost=50.0)
wind = Generator(name="wind", nominal_power=80.0, variable_cost=0.0)

energy_system = EnergySystem(
    portfolio=AssetPortfolio([ccgt, wind, factory]),
    scenarios=Scenario(
        profiles=(
            LoadProfile(load=factory, values=[60, 90, 40, 70]),
            AvailableCapacityProfile(generator=wind, values=[40, 10, 60, 30]),
        ),
    ),
    timestep=timedelta(hours=1),
    number_of_steps=4,
)

result = energy_system.optimize()
print(result.generators.power.unstack())
```

```text
generator  ccgt  wind
time
0          20.0  40.0
1          80.0  10.0
2           0.0  40.0
3          40.0  30.0
```

Notice how the optimizer uses all the wind it can, because it is free, and the CCGT covers the rest. At step 2 the wind could produce 60 MW, but the factory only needs 40.

When the system is created, Odys checks that every load and market has its profile, that no profile points at something outside the system, and that every profile has `number_of_steps` values.

## Multiple scenarios

Use a single `Scenario` for a deterministic problem; its name defaults to `"base"` and its probability to `1.0`. When you need to account for uncertainty, pass a list of scenarios, each with a unique `name` and a `probability`:

```python
low_wind = Scenario(
    name="low_wind",
    probability=0.3,
    profiles=(
        LoadProfile(load=factory, values=[60, 90, 40, 70]),
        AvailableCapacityProfile(generator=wind, values=[20, 5, 30, 15]),
    ),
)
high_wind = Scenario(
    name="high_wind",
    probability=0.7,
    profiles=(
        LoadProfile(load=factory, values=[60, 90, 40, 70]),
        AvailableCapacityProfile(generator=wind, values=[60, 40, 80, 50]),
    ),
)

energy_system = EnergySystem(
    portfolio=AssetPortfolio([ccgt, wind, factory]),
    scenarios=[low_wind, high_wind],
    timestep=timedelta(hours=1),
    number_of_steps=4,
)
```

Odys enforces two rules across the scenarios and raises `OdysValidationError` otherwise:

1. **Probabilities sum to 1.0**, within floating-point tolerance, so 49 scenarios of `1 / 49` each are accepted.
2. **Names are unique.**

Any profile can differ between scenarios, so a single run can capture renewable, demand and price uncertainty at once. A generator without an `AvailableCapacityProfile` in a scenario can produce up to its `nominal_power` in that scenario. See [Stochastic optimization](../optimization/stochastic.md) for how the optimizer weighs the scenarios and which decisions they share.

## Next steps

See [Initial and final conditions](initial_and_final_conditions.md) to set where each asset starts and ends a run.
