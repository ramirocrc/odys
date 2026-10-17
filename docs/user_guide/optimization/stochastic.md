---
icon: lucide/trending-up
---

# Stochastic optimization

Real-world energy systems deal with uncertainty: wind output varies, demand fluctuates, prices change. Stochastic optimization lets you make decisions that account for multiple possible futures simultaneously.

## The idea

Instead of optimizing for a single forecast, you define several **scenarios**, each with a probability. The optimizer finds a plan that maximizes the expected profit over all of them, weighted by their likelihood.

The key modelling choice is which decisions must be made *before* you know which scenario happens. Odys lets you say that per market, with `stage_fixed`; see [below](#what-is-decided-before-and-after-the-uncertainty).

## Scenarios with probabilities

Let's make the wind farm of the [running example](../index.md#the-running-example) uncertain. The site sells in a day-ahead market, where bids are placed the day before, and can rebalance in an intraday market, whose prices depend on how windy the day turns out to be:

```python
from odys import (
    AvailableCapacityProfile,
    EnergyMarket,
    FixedLoad,
    Generator,
    LoadProfile,
    PriceProfile,
    Scenario,
)

ccgt = Generator(name="ccgt", nominal_power=100.0, variable_cost=50.0)
wind = Generator(name="wind", nominal_power=80.0, variable_cost=0.0)
factory = FixedLoad(name="factory")
day_ahead = EnergyMarket(name="day_ahead", max_trading_volume_per_step=150.0, stage_fixed=True)
intraday = EnergyMarket(name="intraday", max_trading_volume_per_step=50.0)

low_wind = Scenario(
    name="low_wind",
    probability=0.3,
    profiles=(
        LoadProfile(load=factory, values=[60, 90, 40, 70]),
        AvailableCapacityProfile(generator=wind, values=[20, 5, 30, 15]),
        PriceProfile(market=day_ahead, values=[40, 75, 30, 65]),
        PriceProfile(market=intraday, values=[55, 90, 45, 70]),
    ),
)
high_wind = Scenario(
    name="high_wind",
    probability=0.7,
    profiles=(
        LoadProfile(load=factory, values=[60, 90, 40, 70]),
        AvailableCapacityProfile(generator=wind, values=[60, 40, 80, 50]),
        PriceProfile(market=day_ahead, values=[40, 75, 30, 65]),
        PriceProfile(market=intraday, values=[30, 60, 20, 45]),
    ),
)
```

The day-ahead prices are already known, so they are the same in both scenarios. See [Scenarios & Profiles](../concepts/scenario.md#multiple-scenarios) for the rules scenarios must follow: probabilities that sum to 1 and unique names.

## Using stochastic scenarios

Pass the list of scenarios instead of a single `Scenario`. Everything else works the same:

```python
from datetime import timedelta

from odys import AssetPortfolio, EnergySystem

energy_system = EnergySystem(
    portfolio=AssetPortfolio([ccgt, wind, factory]),
    markets=[day_ahead, intraday],
    scenarios=[low_wind, high_wind],
    timestep=timedelta(hours=1),
    number_of_steps=4,
)

result = energy_system.optimize()
print(result.markets.net_volume.unstack("scenario"))
```

```text
scenario        low_wind  high_wind
time market
0    day_ahead      50.0       50.0
     intraday       10.0      -50.0
1    day_ahead      65.0       65.0
     intraday      -50.0      -15.0
2    day_ahead      90.0       90.0
     intraday      -50.0      -50.0
3    day_ahead      95.0       95.0
     intraday      -50.0      -50.0
```

Notice that the day-ahead volumes are identical in both scenarios: the site commits to them before it knows the weather. The intraday volumes differ, because the site balances its day-ahead position once the weather is known:

- With low wind, the CCGT runs hard and the site buys the rest of what it sold day-ahead back intraday, at high prices.
- With high wind, intraday power is cheaper than the CCGT at steps 0, 2 and 3, so the site buys as much as the market allows and runs the CCGT less, or not at all.

## What is decided before and after the uncertainty

Every decision in Odys is made **per scenario**, as if the optimizer knew which scenario will happen, except the trades in markets marked `stage_fixed=True`. Those are the same in every scenario: they are decided before the uncertainty is resolved.

| Decision                                                  | Same in every scenario       |
| --------------------------------------------------------- | ---------------------------- |
| Trades in a market with `stage_fixed=True`                | Yes                          |
| Trades in a market with `stage_fixed=False` (the default) | No                           |
| Generator output and on/off status                        | No                           |
| Battery and EV charging and discharging                   | No                           |
| Flexible load adjustments                                 | No                           |
| Initial and final conditions                              | Yes (they are inputs)        |

This is a two-stage problem: the stage-fixed trades are the first stage, and everything else is the second stage, which adapts to each scenario.

Two consequences are worth knowing:

- **Without a stage-fixed market and without a [CVaR term](objective.md#risk-cvar), the scenarios don't interact.** The result is the same as solving each scenario on its own: every scenario gets its own perfect-foresight plan. Use a stage-fixed market to model a commitment you can't take back.
- **Generator commitment adapts to each scenario.** The CCGT above is on in one scenario and off in the other at the same step. If a unit has to be scheduled in advance, model that commitment through a stage-fixed market position.

See [EnergyMarket](../markets/energy_market.md#stage-fixed-markets) for how to set `stage_fixed`, and the [CVaR Market Risk example](../../examples/cvar_market_risk.md) for a full walkthrough.

## Results with multiple scenarios

With several scenarios, every results series gains a `scenario` level. Select one scenario with pandas' `xs`:

```python
print(result.generators.power.xs("high_wind", level="scenario"))
```

```text
time  generator
0     ccgt           0.0
      wind          60.0
1     ccgt         100.0
      wind          40.0
2     ccgt           0.0
      wind          80.0
3     ccgt          65.0
      wind          50.0
Name: power, dtype: float64
```

For single-scenario runs, the scenario level is dropped automatically so you don't have to deal with it.

## One scenario or several

|             | One `Scenario`         | A list of scenarios         |
| ----------- | ---------------------- | --------------------------- |
| Probability | Defaults to 1.0        | Explicit, must sum to 1.0   |
| Name        | Defaults to `"base"`   | Required, must be unique    |
| Use case    | Deterministic dispatch | Decisions under uncertainty |

## Mathematical formulation

Every variable and constraint is indexed by scenario $s$, and the scenario probabilities sum to 1:

$$
\sum_s \pi_s = 1
$$

The risk-neutral objective is the expected profit over the scenarios:

$$
\max \sum_s \pi_s \Pi_s
$$

The scenarios are coupled only through the [non-anticipativity constraints](../../formulation/non_anticipativity.md#na-1) of stage-fixed markets and, when the objective has one, the [CVaR term](objective.md#cvar). To weigh bad outcomes more heavily, add a CVaR term; see [Objective](objective.md).

## Next steps

Next, see [Solvers](solvers.md) to choose and tune the solver behind `.optimize()`.
