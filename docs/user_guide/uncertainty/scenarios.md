---
icon: lucide/trending-up
---

# Scenarios

So far every plan was built on a best guess: one forecast of tomorrow, treated as certain. But tomorrow may be calm or windy, and the prices move with it. Planning against several scenarios, each with a probability, gives you the plan that does best across all of them, instead of one that only works if the forecast is right.

## From a best guess to several futures

Let's take the complete site of the [running example](../index.md#the-running-example) and replace its single forecast with two futures. Tomorrow is calm with probability 0.3, or windy with probability 0.7. The site still bids on the day-ahead market tonight, before it knows which, and can rebalance on an intraday market tomorrow, whose prices follow the wind:

```python
from datetime import timedelta

from odys import (
    AssetPortfolio,
    AvailableCapacityProfile,
    Battery,
    EnergyMarket,
    EnergySystem,
    FixedLoad,
    FlexibleLoad,
    Generator,
    LoadProfile,
    PriceProfile,
    Scenario,
    StationaryStorage,
    StorageInitialState,
)

ccgt = Generator(name="ccgt", nominal_power=100.0, variable_cost=50.0)
wind = Generator(name="wind", nominal_power=80.0, variable_cost=0.0)
factory = FixedLoad(name="factory")
process = FlexibleLoad(name="process", max_increase=20.0, max_decrease=10.0, value_of_consumption=60.0)
bess = StationaryStorage(
    name="bess",
    battery=Battery(
        capacity=50.0,
        max_charge_power=25.0,
        max_discharge_power=25.0,
        efficiency_charging=0.95,
        efficiency_discharging=0.95,
    ),
)
day_ahead = EnergyMarket(name="day_ahead", max_trading_volume_per_step=150.0, stage_fixed=True)
intraday = EnergyMarket(name="intraday", max_trading_volume_per_step=50.0)

calm = Scenario(
    name="calm",
    probability=0.3,
    profiles=(
        LoadProfile(load=factory, values=[60, 90, 40, 70]),
        LoadProfile(load=process, values=[30, 30, 30, 30]),
        AvailableCapacityProfile(generator=wind, values=[20, 5, 30, 15]),
        PriceProfile(market=day_ahead, values=[40, 75, 30, 65]),
        PriceProfile(market=intraday, values=[55, 90, 45, 70]),
    ),
)
windy = Scenario(
    name="windy",
    probability=0.7,
    profiles=(
        LoadProfile(load=factory, values=[60, 90, 40, 70]),
        LoadProfile(load=process, values=[30, 30, 30, 30]),
        AvailableCapacityProfile(generator=wind, values=[60, 40, 80, 50]),
        PriceProfile(market=day_ahead, values=[40, 75, 30, 65]),
        PriceProfile(market=intraday, values=[30, 60, 20, 45]),
    ),
)
```

Each scenario holds a full set of profiles, and any of them can differ: here the wind and the intraday prices do. The day-ahead prices are already known tonight, so they're the same in both. Then pass the list of scenarios where a single `Scenario` went before:

```python
energy_system = EnergySystem(
    portfolio=AssetPortfolio([ccgt, wind, bess, factory, process]),
    markets=[day_ahead, intraday],
    scenarios=[calm, windy],
    timestep=timedelta(hours=1),
    number_of_steps=4,
    initial_conditions=(StorageInitialState(storage=bess, soc=0.5),),
)

result = energy_system.optimize()
print(result.markets.net_volume.unstack("scenario").round(2))
```

```text
scenario          calm   windy
time market
0    day_ahead   -4.09   -4.09
     intraday    10.00  -50.00
1    day_ahead   70.00   70.00
     intraday   -50.00  -15.00
2    day_ahead   15.00   15.00
     intraday   -50.00  -50.00
3    day_ahead  100.00  100.00
     intraday   -50.00  -50.00
```

The day-ahead trades are the same in both scenarios: the site places one set of bids tonight. Intraday, it rebalances once it knows the weather:

- **Calm:** the CCGT runs at full output whenever intraday costs more than it does, and the site buys back on intraday the rest of what it sold day-ahead. At step 0, intraday pays 55 $/MWh, above the CCGT's cost, so the site sells 10 MW there too. At step 2 it costs only 45, so the site buys the full 50 MW and runs the CCGT at half.
- **Windy:** intraday power is cheap, so the site buys as much as the market allows at steps 0, 2 and 3, and runs the CCGT less, or not at all.

Scenario names have to be unique, and the probabilities have to add up to 1, within floating-point tolerance: 49 scenarios of `1 / 49` each are accepted. A generator without an `AvailableCapacityProfile` in a scenario can produce up to its `nominal_power` in that scenario.

## What's decided before the uncertainty

The bids go in tonight; the wind is known tomorrow morning. Everything you can still change once you know it adapts to each scenario. The decisions you can't wait on are the same in all of them:

| Decision | Same in every scenario |
| -------- | ---------------------- |
| Trades on a market with `stage_fixed=True` | Yes: decided before the uncertainty |
| Trades on any other market | No |
| Generator output and on/off status | No |
| Battery and vehicle charging and discharging | No |
| Flexible load adjustments | No |

Mark a market `stage_fixed` when you commit to it before you know the outcome, like day-ahead; see [Stage-fixed markets](../markets/energy_market.md#stage-fixed-markets) and [NA-1](../../formulation/non_anticipativity.md#na-1). Initial and final conditions are the same in every scenario too, because they're inputs.

Two consequences to keep in mind:

- **Without a stage-fixed market or a risk term, the scenarios don't interact.** Each scenario gets the plan that's best for it alone, as if the optimizer knew in advance which future would happen. The result is the same as solving each one on its own. See [When scenarios are solved on their own](../../formulation/scenarios.md#when-scenarios-are-solved-on-their-own).
- **Generator commitment adapts to each scenario.** The CCGT above is on at step 0 when it's calm and off when it's windy. A unit that has to be scheduled in advance isn't modelled as such today; see [NA-1](../../formulation/non_anticipativity.md#na-1).

## Results per scenario

With several scenarios, every series gains a `scenario` level. Select one scenario with pandas' `xs`:

```python
print(result.generators.power.xs("windy", level="scenario"))
```

```text
time  generator
0     ccgt           0.0
      wind          60.0
1     ccgt         100.0
      wind          40.0
2     ccgt           0.0
      wind          80.0
3     ccgt          95.0
      wind          50.0
Name: power, dtype: float64
```

To get the expected value of a series, weigh each scenario by its probability:

```python
import pandas as pd

probabilities = pd.Series({calm.name: calm.probability, windy.name: windy.probability})
print(result.generators.power.unstack("scenario").mul(probabilities).sum(axis=1).round(2))
```

```text
time  generator
0     ccgt          30.0
      wind          48.0
1     ccgt         100.0
      wind          29.5
2     ccgt          15.0
      wind          65.0
3     ccgt          96.5
      wind          39.5
dtype: float64
```

`result.objective_value` is the expected profit, weighted the same way. With a single scenario, the scenario level is dropped, as on every other page.

## Next steps

The plan above maximizes the expected profit, so a bad calm day is fine as long as the windy days make up for it. To weigh bad outcomes more heavily, see [Risk (CVaR)](risk.md).
