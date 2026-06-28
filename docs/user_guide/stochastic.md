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

## StochasticScenario

Each scenario extends the base `Scenario` with a name and a probability:

```python
from odys import StochasticScenario

low_wind = StochasticScenario(
    name="low_wind",
    probability=0.3,
    available_capacity_profiles={
        "wind_farm": [30, 20, 40, 25, 35, 30, 20],
    },
    load_profiles={
        "load": [180, 180, 150, 50, 80, 90, 100],
    },
)

high_wind = StochasticScenario(
    name="high_wind",
    probability=0.7,
    available_capacity_profiles={
        "wind_farm": [120, 140, 100, 130, 110, 150, 140],
    },
    load_profiles={
        "load": [180, 180, 150, 50, 80, 90, 100],
    },
)
```

### Available fields

Each `StochasticScenario` has:

| Field                         | Type                     | Required | Description                                                  |
| ----------------------------- | ------------------------ | -------- | ------------------------------------------------------------ |
| `name`                        | `str`                    | Yes      | Unique name for the scenario                                 |
| `probability`                 | `float`                  | Yes      | Probability (0-1) of this scenario occurring                 |
| `load_profiles`               | `dict[str, list[float]]` | No       | Load values per timestep, keyed by load name                 |
| `available_capacity_profiles` | `dict[str, list[float]]` | No       | Max available capacity per timestep, keyed by generator name |
| `market_prices`               | `dict[str, list[float]]` | No       | Market prices per timestep, keyed by market name             |

!!! warning

    Probabilities across all scenarios must sum to exactly 1.0 and scenario names must be unique. Odys validates both.

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

You can vary any combination of:

- **`available_capacity_profiles`** -- model different wind/solar outputs
- **`load_profiles`** -- model demand uncertainty
- **`market_prices`** -- model price volatility

Anything you don't include in a scenario stays unconstrained (e.g., if you don't specify `available_capacity_profiles`, generators can produce up to their `nominal_power` in that scenario).

## Scenario vs StochasticScenario

|             | `Scenario`             | `StochasticScenario`        |
| ----------- | ---------------------- | --------------------------- |
| Number      | Exactly one            | Two or more in a list       |
| Probability | Implicit 1.0           | Explicit, must sum to 1.0   |
| Name        | Not needed             | Required, must be unique    |
| Use case    | Deterministic dispatch | Decisions under uncertainty |

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

When you have multiple scenarios, the results DataFrames include a scenario dimension:

```python
result = energy_system.optimize()

# Generator power now has a scenario axis
print(result.generators.power)

# The combined DataFrame includes the scenario level
print(result.to_dataframe)
```

For deterministic (single scenario) runs, the scenario level is dropped automatically so you don't have to deal with it.

## Next steps

For a deeper dive into the `StochasticScenario` class and its validation rules, see [StochasticScenario](stochastic_scenario.md).
