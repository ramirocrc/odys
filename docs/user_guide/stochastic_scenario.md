# StochasticScenario

A `StochasticScenario` extends [Scenario](scenario.md) with a name and a probability, letting you model multiple possible futures. The optimizer finds a dispatch plan that performs well across all scenarios, weighted by how likely each one is.

## Basic usage

```python
from odys.energy_system_models.scenarios import StochasticScenario

low_wind = StochasticScenario(
    name="low_wind",
    probability=0.3,
    available_capacity_profiles={
        "wind_farm": [30, 20, 40, 25],
    },
    load_profiles={"demand": [100, 120, 80, 90]},
)

high_wind = StochasticScenario(
    name="high_wind",
    probability=0.7,
    available_capacity_profiles={
        "wind_farm": [120, 140, 100, 130],
    },
    load_profiles={"demand": [100, 120, 80, 90]},
)
```

## Fields

`StochasticScenario` inherits all fields from [Scenario](scenario.md) and adds two:

| Field                         | Type                     | Required | Default | Description                                                  |
| ----------------------------- | ------------------------ | -------- | ------- | ------------------------------------------------------------ |
| `name`                        | `str`                    | Yes      | -       | Unique identifier for the scenario                           |
| `probability`                 | `float`                  | Yes      | -       | Probability (0-1) of this scenario occurring                 |
| `load_profiles`               | `dict[str, list[float]]` | No       | `None`  | Load values per timestep, keyed by load name                 |
| `available_capacity_profiles` | `dict[str, list[float]]` | No       | `None`  | Max available capacity per timestep, keyed by generator name |
| `market_prices`               | `dict[str, list[float]]` | No       | `None`  | Market prices per timestep, keyed by market name             |

## Validation rules

Odys enforces two rules when you pass a list of stochastic scenarios to the `EnergySystem`:

1. **Probabilities must sum to 1.0** -- if they don't, you'll get a `ValueError`
2. **Names must be unique** -- duplicated names also raise a `ValueError`

```python
# This will fail: probabilities sum to 0.8
scenarios = [
    StochasticScenario(name="a", probability=0.5, load_profiles={"demand": [100]}),
    StochasticScenario(name="b", probability=0.3, load_profiles={"demand": [100]}),
]

# This will fail: duplicate names
scenarios = [
    StochasticScenario(name="scenario", probability=0.5, load_profiles={"demand": [100]}),
    StochasticScenario(name="scenario", probability=0.5, load_profiles={"demand": [100]}),
]
```

## Using stochastic scenarios

Pass a list of scenarios to the [EnergySystem](energy_system.md) instead of a single `Scenario`:

```python
from datetime import timedelta

from odys.energy_system import EnergySystem

energy_system = EnergySystem(
    portfolio=portfolio,
    scenarios=[low_wind, high_wind],
    timestep=timedelta(hours=1),
    number_of_steps=4,
    power_unit="MW",
)

result = energy_system.optimize()
```

Everything else works the same -- the optimizer just considers multiple futures instead of one.

## What can vary across scenarios

Each scenario can have different values for any combination of:

- **`available_capacity_profiles`** -- model different wind/solar outputs
- **`load_profiles`** -- model demand uncertainty
- **`market_prices`** -- model price volatility

This means you can capture several types of uncertainty in a single optimization run.

## Scenario vs StochasticScenario

|             | `Scenario`             | `StochasticScenario`        |
| ----------- | ---------------------- | --------------------------- |
| Number      | Exactly one            | Two or more in a list       |
| Probability | Implicit 1.0           | Explicit, must sum to 1.0   |
| Name        | Not needed             | Required, must be unique    |
| Use case    | Deterministic dispatch | Decisions under uncertainty |

## Next steps

For a deeper dive into stochastic optimization concepts -- stage-fixed decisions, results with multiple scenarios, and how the optimizer weighs probabilities -- see [Stochastic Optimization](../user_guide/stochastic.md).
