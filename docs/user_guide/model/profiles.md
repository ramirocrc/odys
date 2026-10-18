---
icon: lucide/file-text
---

# Profiles

A plan needs to know what tomorrow looks like: how much the factory will draw, how much the wind will blow, what the market will pay. A `Scenario` holds that best guess, as a set of **profiles**: one time series per asset or market, with one value per step. A deterministic plan takes a single `Scenario`.

## Assets and profiles

An asset holds its intrinsic specifications, the things that stay the same whatever happens tomorrow: a thermal plant's nominal power, a battery's capacity. A profile sets the conditions you plan the system under, step by step: the demand to serve, the prices on offer, what a unit can produce at each step.

So the same CCGT can be planned under very different conditions. Say half of it is in maintenance from the third hour: its `nominal_power` stays 100 MW, and an `AvailableCapacityProfile` caps what it can produce while the work lasts:

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

Each profile holds the asset or market itself, not its name, so it can't be attached to the wrong kind of object.

## Profile types

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

A best guess is one future. To plan against several, each with its own probability, see [Scenarios](../uncertainty/scenarios.md); a single `Scenario` is named `"base"` and has a probability of 1.

## Next steps

The model has its time series. Next, meet the assets one by one, starting with the [Generator](../assets/generator.md).
