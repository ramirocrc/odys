# Scenario

A `Scenario` defines the operating conditions for your energy system -- load demand, generator availability, and market prices over time. It's the bridge between your asset definitions and the actual timeseries data the optimizer works with.

## Basic usage

```python
from odys.energy_system_models.scenarios import Scenario

scenario = Scenario(
    load_profiles={"demand": [60, 90, 40, 70]},
)
```

This tells the optimizer: "here's what demand looks like over four timesteps." The key `"demand"` must match the `name` of a `Load` in your portfolio.

## Fields

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `load_profiles` | `dict[str, list[float]]` | No | `None` | Load values per timestep, keyed by load name |
| `available_capacity_profiles` | `dict[str, list[float]]` | No | `None` | Max available capacity per timestep, keyed by generator name |
| `market_prices` | `dict[str, list[float]]` | No | `None` | Market prices per timestep, keyed by market name |

All fields are optional -- you only include what you need. If a field is omitted, the optimizer won't apply that constraint (e.g., generators without an `available_capacity_profiles` entry can produce up to their `nominal_power`).

## Load profiles

Specify how much power each load demands at each timestep:

```python
scenario = Scenario(
    load_profiles={
        "factory": [100, 120, 80, 90],
        "office": [20, 25, 15, 20],
    },
)
```

The keys must match the `name` of a [Load](load.md) in your portfolio.

## Available capacity profiles

Cap the output of specific generators over time. This is how you model variable renewable generation like wind or solar:

```python
scenario = Scenario(
    available_capacity_profiles={
        "wind_farm": [80, 60, 90, 70],
        "solar": [0, 50, 80, 30],
    },
    load_profiles={"demand": [100, 120, 80, 90]},
)
```

The keys must match the `name` of a [PowerGenerator](power_generator.md) in your portfolio. At each timestep, the generator can't produce more than the value specified here (or its `nominal_power`, whichever is lower).

## Market prices

Provide price timeseries for each [Market](market.md):

```python
scenario = Scenario(
    market_prices={
        "day_ahead": [50, 55, 45, 60],
    },
    load_profiles={"demand": [100, 120, 80, 90]},
)
```

The keys must match the `name` of an `EnergyMarket` passed to the `EnergySystem`.

## Putting it all together

A scenario with all three fields might look like:

```python
from odys.energy_system_models.scenarios import Scenario

scenario = Scenario(
    load_profiles={
        "demand": [100, 120, 80, 90],
    },
    available_capacity_profiles={
        "wind_farm": [80, 60, 90, 70],
    },
    market_prices={
        "day_ahead": [50, 55, 45, 60],
    },
)
```

Then pass it to the [EnergySystem](energy_system.md):

```python
energy_system = EnergySystem(
    portfolio=portfolio,
    scenarios=scenario,
    timestep=timedelta(hours=1),
    number_of_steps=4,
    power_unit="MW",
)
```

## When you need multiple scenarios

A single `Scenario` represents one deterministic future. If you want to optimize under uncertainty -- accounting for multiple possible outcomes -- use [StochasticScenario](stochastic_scenario.md) instead.
