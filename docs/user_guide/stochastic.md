---
icon: lucide/trending-up
---

# Stochastic Optimization

Real-world energy systems deal with uncertainty -- wind output varies, demand fluctuates, prices change. Stochastic optimization lets you make decisions that account for multiple possible futures simultaneously.

See [Mathematical notation](mathematical_notation.md) for the full list of symbols used below.

## The idea

Instead of optimizing for a single forecast, let's define multiple **scenarios**, each with a probability. The optimizer finds a dispatch plan that performs well across all scenarios, weighted by their likelihood:

$$
\sum_s \pi_s = 1
$$

The risk-neutral objective becomes an expected value over those scenarios:

$$
\max \sum_s \pi_s \Pi_s
$$

## Scenarios with probabilities

Each scenario gets a unique name and a probability. Its profiles reference the assets they describe:

```python
from odys import AvailableCapacityProfile, LoadProfile, FixedLoad, Generator, Scenario

wind_farm = Generator(name="wind_farm", nominal_power=150.0, variable_cost=0.0)
load = FixedLoad(name="load")

low_wind = Scenario(
    name="low_wind",
    probability=0.3,
    profiles=(
        AvailableCapacityProfile(generator=wind_farm, values=[30, 20, 40, 25, 35, 30, 20]),
        LoadProfile(load=load, values=[180, 180, 150, 50, 80, 90, 100]),
    ),
)

high_wind = Scenario(
    name="high_wind",
    probability=0.7,
    profiles=(
        AvailableCapacityProfile(generator=wind_farm, values=[120, 140, 100, 130, 110, 150, 140]),
        LoadProfile(load=load, values=[180, 180, 150, 50, 80, 90, 100]),
    ),
)
```

!!! warning

    Probabilities across all scenarios must sum to 1.0 (within floating-point tolerance) and scenario names must be unique. Odys validates both.

See [Scenario](scenario.md) for every field and profile type.

## Using stochastic scenarios

Pass a list of scenarios instead of a single `Scenario`. Use this when you have multiple plausible futures and want to optimize across all of them.

```python
from datetime import timedelta

from odys import EnergySystem

energy_system = EnergySystem(
    portfolio=portfolio,
    scenarios=[low_wind, high_wind],
    timestep=timedelta(minutes=30),
    number_of_steps=7,
)

result = energy_system.optimize()
```

Everything else works the same -- the optimizer just considers multiple futures instead of one.

## What varies across scenarios

You can vary any profile between scenarios:

- **`AvailableCapacityProfile`** -- model different wind/solar outputs
- **`LoadProfile`** of a fixed load -- model demand uncertainty
- **`LoadProfile`** of a flexible load -- model flexible demand uncertainty
- **`PriceProfile`** -- model price volatility

A generator without an `AvailableCapacityProfile` in a scenario can produce up to its `nominal_power` in that scenario.

## One scenario or several

|             | One `Scenario`             | A list of scenarios            |
| ----------- | -------------------------- | ------------------------------ |
| Probability | Defaults to 1.0            | Explicit, must sum to 1.0      |
| Name        | Defaults to `"base"`       | Required, must be unique       |
| Use case    | Deterministic dispatch     | Decisions under uncertainty    |

## Stage-fixed decisions

When using stochastic optimization with markets, you can mark certain markets as `stage_fixed=True`. Use this when the optimizer must commit to the same trading volumes in that market across all scenarios -- modeling situations where you lock in a position before uncertainty resolves.

Mathematically, each stage-fixed market variable is pinned to its first-scenario value:

$$
x_{m,t,s} = x_{m,t,s_0} \quad \forall s
$$

This is applied to market buy volume, sell volume, and trade mode.

```python
from odys import EnergyMarket

day_ahead = EnergyMarket(
    name="day_ahead",
    max_trading_volume_per_step=150.0,
    stage_fixed=True,  # must be the same in all scenarios
)

intraday = EnergyMarket(
    name="intraday",
    max_trading_volume_per_step=50.0,
    # stage_fixed=False by default -- can differ per scenario
)
```

See the [CVaR Market Risk example](../examples/cvar_market_risk.md) for a full walkthrough.

## Results with multiple scenarios

When you have multiple scenarios, every results series includes a scenario level:

```python
result = energy_system.optimize()

# Generator power now has a scenario axis
print(result.generators.power)

# Or as a DataFrame / Dataset
print(result.generators.to_dataframe())
print(result.to_dataset())
```

For deterministic (single scenario) runs, the scenario level is dropped automatically so you don't have to deal with it.

## Next steps

For the rules that scenarios must follow, see [Scenario](scenario.md#multiple-scenarios).
