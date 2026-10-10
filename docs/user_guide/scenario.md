---
icon: lucide/file-text
---

# Scenario

A `Scenario` describes the operating conditions of your energy system over time: how much each load demands, how much each generator can produce, and what each market pays. Each time series is a **profile** that points at the asset or market it belongs to.

## Basic usage

Let's describe the demand of one load over four timesteps.

```python
from odys import LoadProfile, FixedLoad, Scenario

demand = FixedLoad(name="demand")

scenario = Scenario(
    profiles=(LoadProfile(load=demand, values=[60, 90, 40, 70]),),
)
```

This tells the optimizer: "here's what `demand` consumes over four timesteps." The profile holds the load object itself, so it cannot be attached to the wrong kind of asset, and a typo in a name string is no longer possible.

## Fields

| Field         | Type                  | Required | Default  | Description                                           |
| ------------- | --------------------- | -------- | -------- | ----------------------------------------------------- |
| `name`        | `str`                 | No       | `"base"` | Unique identifier of the scenario                     |
| `probability` | `float`               | No       | `1.0`    | Probability (0-1) of the scenario                     |
| `profiles`    | `tuple` of profiles   | No       | `()`     | Time series of the scenario's assets and markets      |

Every profile has one value per optimization timestep, so its length must equal `number_of_steps`. Each asset or market has at most one profile of each kind per scenario.

## Profiles

| Profile                    | References   | Unit         | Required in every scenario | Meaning                                                      |
| -------------------------- | ------------ | ------------ | -------------------------- | ------------------------------------------------------------ |
| `LoadProfile`              | `load=`      | MW           | Yes, for every load        | Demand of a `FixedLoad`, or base profile of a `FlexibleLoad` |
| `AvailableCapacityProfile` | `generator=` | MW           | No                         | Upper bound on a generator's output at each timestep         |
| `PriceProfile`             | `market=`    | currency/MWh | Yes, for every market      | Price of an `EnergyMarket` at each timestep                  |

### Demand of a fixed load

Every [FixedLoad](load.md#fixed-loads) in the portfolio needs a `LoadProfile` in every scenario:

```python
from odys import LoadProfile, FixedLoad, Scenario

factory = FixedLoad(name="factory")
office = FixedLoad(name="office")

scenario = Scenario(
    profiles=(
        LoadProfile(load=factory, values=[100, 120, 80, 90]),
        LoadProfile(load=office, values=[20, 25, 15, 20]),
    ),
)
```

### Base demand of a flexible load

For a [FlexibleLoad](load.md#flexible-loads), `LoadProfile` is the base profile. The optimizer can adjust consumption up or down from it:

```python
from odys import LoadProfile, FlexibleLoad, Scenario

process = FlexibleLoad(name="industrial_process", max_increase=20, max_decrease=10, value_of_consumption=60)

scenario = Scenario(
    profiles=(LoadProfile(load=process, values=[80, 80, 80, 80]),),
)
```

### Available capacity of a generator

Cap the output of specific generators over time. This is how you model variable renewable generation like wind or solar:

```python
from odys import AvailableCapacityProfile, LoadProfile, FixedLoad, Generator, Scenario

wind = Generator(name="wind_farm", nominal_power=100, variable_cost=0)
solar = Generator(name="solar", nominal_power=100, variable_cost=0)
demand = FixedLoad(name="demand")

scenario = Scenario(
    profiles=(
        AvailableCapacityProfile(generator=wind, values=[80, 60, 90, 70]),
        AvailableCapacityProfile(generator=solar, values=[0, 50, 80, 30]),
        LoadProfile(load=demand, values=[100, 120, 80, 90]),
    ),
)
```

At each timestep, the generator can't produce more than this value. Each value must lie between 0 and the generator's `nominal_power`. A generator without an `AvailableCapacityProfile` can produce up to its `nominal_power`.

### Price of a market

Provide a price time series for each [EnergyMarket](market.md) passed to the `EnergySystem`:

```python
from odys import LoadProfile, EnergyMarket, FixedLoad, PriceProfile, Scenario

day_ahead = EnergyMarket(name="day_ahead", max_trading_volume_per_step=200)
demand = FixedLoad(name="demand")

scenario = Scenario(
    profiles=(
        PriceProfile(market=day_ahead, values=[50, 55, 45, 60]),
        LoadProfile(load=demand, values=[100, 120, 80, 90]),
    ),
)
```

## Putting it all together

Build the assets and markets first, then a scenario that references them, and pass both to the [EnergySystem](energy_system.md):

```python
from datetime import timedelta

from odys import (
    AssetPortfolio,
    AvailableCapacityProfile,
    LoadProfile,
    EnergyMarket,
    EnergySystem,
    FixedLoad,
    FlexibleLoad,
    Generator,
    PriceProfile,
    Scenario,
)

wind = Generator(name="wind_farm", nominal_power=100, variable_cost=0)
demand = FixedLoad(name="demand")
process = FlexibleLoad(name="industrial_process", max_increase=20, max_decrease=10, value_of_consumption=60)
day_ahead = EnergyMarket(name="day_ahead", max_trading_volume_per_step=200)

scenario = Scenario(
    profiles=(
        LoadProfile(load=demand, values=[100, 120, 80, 90]),
        LoadProfile(load=process, values=[80, 80, 80, 80]),
        AvailableCapacityProfile(generator=wind, values=[80, 60, 90, 70]),
        PriceProfile(market=day_ahead, values=[50, 55, 45, 60]),
    ),
)

energy_system = EnergySystem(
    portfolio=AssetPortfolio([wind, demand, process]),
    markets=day_ahead,
    scenarios=scenario,
    timestep=timedelta(hours=1),
    number_of_steps=4,
)
```

When the system is created, Odys checks that every load and market has its profile, that no profile points at something outside the system, and that every profile has `number_of_steps` values.

## Multiple scenarios

A single `Scenario` is one deterministic future; its name defaults to `"base"` and its probability to `1.0`. To optimize under uncertainty, pass a list of scenarios, each with a unique `name` and a `probability`:

```python
gas = Generator(name="gas", nominal_power=150, variable_cost=60)

low_wind = Scenario(
    name="low_wind",
    probability=0.3,
    profiles=(
        AvailableCapacityProfile(generator=wind, values=[30, 20, 40, 25]),
        LoadProfile(load=demand, values=[100, 120, 80, 90]),
    ),
)
high_wind = Scenario(
    name="high_wind",
    probability=0.7,
    profiles=(
        AvailableCapacityProfile(generator=wind, values=[80, 90, 100, 95]),
        LoadProfile(load=demand, values=[100, 120, 80, 90]),
    ),
)

energy_system = EnergySystem(
    portfolio=AssetPortfolio([wind, gas, demand]),
    scenarios=[low_wind, high_wind],
    timestep=timedelta(hours=1),
    number_of_steps=4,
)
```

Odys enforces two rules across the scenarios and raises `OdysValidationError` otherwise:

1. **Probabilities sum to 1.0**, within floating-point tolerance, so 49 scenarios of `1 / 49` each are accepted.
2. **Names are unique.**

Any profile can differ between scenarios, so a single run can capture renewable, demand and price uncertainty at once. See [Stochastic Optimization](stochastic.md) for how the optimizer weighs the scenarios.

## Next steps

Ready to run your first optimization? See [Optimization](optimization.md) to understand the objective function, constraints, and how to read results.
