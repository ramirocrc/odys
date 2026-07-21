---
icon: fontawesome/solid/plug
---

# Load

Loads represent energy demand that the system must satisfy. Odys supports two types: **fixed loads** (inelastic demand) and **flexible loads** (adjustable demand).

## Fixed loads

A fixed load represents inelastic demand that must be met exactly. The optimizer cannot adjust it — it must dispatch generators, batteries, and markets to match.

```python
from odys import FixedLoad

load = FixedLoad(name="factory_demand")
```

The actual demand values are specified later in the `Scenario` via `fixed_load_profiles`. We separate the load definition from its time series because the same load can appear in multiple scenarios with different profiles.

### Fixed load profiles

In your scenario, provide the demand time series keyed by the load's name:

```python
from odys import Scenario

scenario = Scenario(
    fixed_load_profiles={"factory_demand": [100, 120, 80, 90]},
)
```

For multiple fixed loads, add more entries:

```python
scenario = Scenario(
    fixed_load_profiles={
        "factory": [100, 120, 80, 90],
        "office": [20, 25, 15, 20],
    },
)
```

## Flexible loads

A flexible load gives the optimizer room to adjust demand up or down within bounds. Use this for demand response programs, industrial processes that can shift load, or any consumption that has economic value but timing flexibility.

```python
from odys import FlexibleLoad

flexible_load = FlexibleLoad(
    name="industrial_process",
    max_increase=50.0,
    max_decrease=30.0,
    value_of_consumption=100.0,
)
```

### Fields

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `name` | `str` | Yes | Unique identifier for the load |
| `max_increase` | `float` | Yes | Maximum MW the load can increase above the base profile (must be > 0) |
| `max_decrease` | `float` | Yes | Maximum MW the load can decrease below the base profile (must be > 0) |
| `value_of_consumption` | `float` | Yes | Economic value of consuming electricity in currency per MWh (must be >= 0) |

### Flexible load base profiles

Like fixed loads, flexible loads require a time series in the scenario. This is the **base profile** — the demand the optimizer starts from before making adjustments:

```python
scenario = Scenario(
    flexible_load_base_profiles={"industrial_process": [80, 80, 80, 80]},
)
```

### How flexible loads work

The optimizer introduces a decision variable `load_adjustment` for each flexible load at each timestep. The actual consumption becomes:

```
actual_consumption = base_profile + load_adjustment
```

The adjustment is bounded:

```
-max_decrease <= load_adjustment <= max_increase
```

The optimizer decides whether to increase or decrease load based on economics. The profit contribution is:

```
profit += load_adjustment * value_of_consumption
```

The procurement cost of adjusting load is captured implicitly through the power balance constraint: when the optimizer increases load, it must procure more energy from generators or markets (whose costs are already in the objective). When it decreases load, it frees up supply for other uses (e.g., selling to markets).

**Decision logic:**
- When `value_of_consumption` exceeds the marginal supply cost, increasing load is profitable
- When the marginal supply cost exceeds `value_of_consumption`, decreasing load saves money

### Example: flexible load with market

```python
from datetime import timedelta
from odys import (
    AssetPortfolio,
    EnergyMarket,
    EnergySystem,
    FlexibleLoad,
    Generator,
    Scenario,
)

# Generator with variable cost = 30 $/MWh
generator = Generator(name="gen1", nominal_power=200, variable_cost=30)

# Flexible load: can adjust ±50 MW, values consumption at 100 $/MWh
flexible_load = FlexibleLoad(
    name="flex_load",
    max_increase=50.0,
    max_decrease=50.0,
    value_of_consumption=100.0,
)

market = EnergyMarket(name="market", max_trading_volume_per_step=1000)

portfolio = AssetPortfolio([generator, flexible_load])

# Market price = 20 $/MWh (below generator cost)
# Since voc (100) > marginal cost (30), optimizer will increase load
system = EnergySystem(
    portfolio=portfolio,
    markets=market,
    timestep=timedelta(hours=1),
    number_of_steps=4,
    scenarios=Scenario(
        flexible_load_base_profiles={"flex_load": [80, 80, 80, 80]},
        market_prices={"market": [20, 20, 20, 20]},
    ),
)

results = system.optimize()
```

## Combining fixed and flexible loads

You can mix both types in the same portfolio:

```python
from odys import AssetPortfolio, FixedLoad, FlexibleLoad

fixed_load = FixedLoad(name="critical_demand")
flexible_load = FlexibleLoad(
    name="adjustable_demand",
    max_increase=30.0,
    max_decrease=20.0,
    value_of_consumption=75.0,
)

portfolio = AssetPortfolio([fixed_load, flexible_load])

scenario = Scenario(
    fixed_load_profiles={"critical_demand": [100, 100, 100, 100]},
    flexible_load_base_profiles={"adjustable_demand": [50, 50, 50, 50]},
)
```

## Next steps

Ready to add time-shifting to your portfolio? See [Storage](storage.md) to model batteries and other energy storage systems.
