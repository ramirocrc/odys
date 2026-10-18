---
icon: lucide/file-text
---

# Scenario

An asset holds its technical specifications, the things that stay the same whatever happens tomorrow: a thermal plant's nominal power, a battery's capacity. A `Scenario` holds what the system faces over the horizon: what each unit can produce, the demand to serve and the prices on offer. A deterministic plan takes a single `Scenario`, your best guess of tomorrow.

## What a scenario describes

Keeping the two apart means the same assets can be planned under very different circumstances. A scenario describes three things, step by step:

- **Availability**: what a generator can produce. A wind or solar farm follows the weather forecast, and a unit in planned maintenance can only run part of its capacity.
- **Demand**: what each load draws.
- **Prices**: what each market is forecast to pay.

Say half of the CCGT is in maintenance from the third hour. Its `nominal_power` stays 100 MW, and the scenario caps what it can produce while the work lasts:

```python
from odys import AvailableCapacityProfile, FixedLoad, Generator, LoadProfile, Scenario

ccgt = Generator(name="ccgt", nominal_power=100.0, variable_cost=50.0)
factory = FixedLoad(name="factory")

tomorrow = Scenario(
    profiles=(
        LoadProfile(load=factory, values=[60, 90, 40, 70]),
        AvailableCapacityProfile(generator=ccgt, values=[100, 100, 50, 50]),  # half in maintenance from step 2
    ),
)
```

Where an asset starts, such as the battery's charge at midnight, isn't part of a scenario: you know it when you plan, so it's the same in every future. It goes to the `EnergySystem`, see [Initial and final conditions](first_model.md#initial-and-final-conditions).

## Each one is a profile

A scenario holds its availability, demand and prices as **profiles**: one time series per asset or market, with one value per step. Each profile holds the asset or market itself, not its name, so it can't be attached to the wrong kind of object.

| Profile                    | References   | Unit         | Required                   | Meaning                                                                                                                              |
| -------------------------- | ------------ | ------------ | -------------------------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| `LoadProfile`              | `load=`      | MW           | Yes, for every load        | Demand of a [FixedLoad](../assets/fixed_load.md#profiles), or base profile of a [FlexibleLoad](../assets/flexible_load.md#profiles) |
| `AvailableCapacityProfile` | `generator=` | MW           | No                         | What a [Generator](../assets/generator.md#profiles) can produce at each step; up to its `nominal_power` without one                 |
| `PriceProfile`             | `market=`    | currency/MWh | Yes, for every market      | Price of an [EnergyMarket](../markets/energy_market.md#profiles) at each step                                                       |

Every profile has one value per step of the horizon, and each asset or market takes at most one profile of each type. Storage, electric vehicles and chargers take none. The linked sections show each profile in use, with the checks it has to pass.

## Example

Let's add a wind farm to [the first model](first_model.md#basic-usage). Its output depends on the weather, so its `AvailableCapacityProfile` holds tomorrow's wind forecast:

```python
from datetime import timedelta

from odys import AssetPortfolio, EnergySystem

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

The wind is free, so the optimizer uses all of it it can, and the CCGT covers the rest. At step 2 the wind could produce 60 MW, but the factory only needs 40, so 20 MW of wind goes unused.

## One scenario, or several

A single `Scenario` is one possible future, named `"base"` with a probability of 1. Tomorrow may be calm or windy, though, and the prices move with the wind. To plan against several futures, each with its own probability, pass a list of scenarios: see [Several scenarios](../uncertainty/scenarios.md).

## Next steps

The model knows what it faces. Next, meet the assets one by one, starting with the [Generator](../assets/generator.md).
