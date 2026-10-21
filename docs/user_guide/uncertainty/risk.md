---
icon: lucide/target
---

# Risk (CVaR)

By default, odys maximizes the expected profit: a bad day is fine as long as the good days make up for it. That's the right plan if you can live with the bad days. When you can't, because a bad day would hurt more than a good one helps, add a risk term: the conditional value at risk (CVaR), the average profit of your worst futures. The optimizer then gives up some expected profit to make the bad days less bad.

A risk term only matters with [several scenarios](scenarios.md): with a single scenario, the worst outcome is the only outcome.

## Basic usage

Let's take the calm and windy site of the [Several scenarios](scenarios.md) page:

??? example "The site, with a calm and a windy tomorrow"

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
        FlexibleLoadProfile,
        Generator,
        LoadProfile,
        PriceProfile,
        Scenario,
        BatteryStorage,
        StorageInitialState,
    )

    ccgt = Generator(name="ccgt", nominal_power=100.0, variable_cost=50.0)
    wind = Generator(name="wind", nominal_power=80.0, variable_cost=0.0)
    factory = FixedLoad(name="factory")
    process = FlexibleLoad(name="process", value_of_consumption=60.0)
    bess = BatteryStorage(
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
            FlexibleLoadProfile(load=process, lower_bound=[20, 20, 20, 20], upper_bound=[50, 50, 50, 50]),
            AvailableCapacityProfile(generator=wind, values=[20, 5, 30, 15]),
            PriceProfile(market=day_ahead, values=[45, 80, 35, 68]),
            PriceProfile(market=intraday, values=[55, 90, 45, 70]),
        ),
    )
    windy = Scenario(
        name="windy",
        probability=0.7,
        profiles=(
            LoadProfile(load=factory, values=[60, 90, 40, 70]),
            FlexibleLoadProfile(load=process, lower_bound=[20, 20, 20, 20], upper_bound=[50, 50, 50, 50]),
            AvailableCapacityProfile(generator=wind, values=[60, 40, 80, 50]),
            PriceProfile(market=day_ahead, values=[35, 65, 25, 55]),
            PriceProfile(market=intraday, values=[30, 58, 20, 45]),
        ),
    )
    ```

The objective is an `Objective` with a `ProfitTerm` and a `CVaRTerm`, passed to the `EnergySystem`. Let's solve the site twice, once with the default objective and once with a risk term, and compare the day-ahead bids:

```python
import pandas as pd

from odys import CVaRTerm, Objective, ProfitTerm

risk_averse = Objective(
    terms=(
        ProfitTerm(weight=1.0),
        CVaRTerm(weight=0.5, confidence_level=0.9),
    ),
)



def solve_site(objective):
    return EnergySystem(
        portfolio=AssetPortfolio([ccgt, wind, bess, factory, process]),
        markets=[day_ahead, intraday],
        scenarios=[calm, windy],
        timestep=timedelta(hours=1),
        number_of_steps=4,
        initial_conditions=(StorageInitialState(storage=bess, soc=0.5),),
        objective=objective,
    ).optimize()


neutral_result = solve_site(Objective())
averse_result = solve_site(risk_averse)


def day_ahead_bids(result):
    return result.markets.net_volume.xs(("day_ahead", "calm"), level=("market", "scenario"))


print(pd.DataFrame({"risk_neutral": day_ahead_bids(neutral_result), "risk_averse": day_ahead_bids(averse_result)}).round(2))
```

```text
      risk_neutral  risk_averse
time
0            -4.09      -104.09
1            70.00       -25.00
2           -35.00       -85.00
3           100.00       100.00
```

The bids are the same in both scenarios, so we read them from one. Here the worst future is the calm one: the CCGT has to run, and intraday power is dear. The risk-neutral plan sells most of its volume day-ahead and buys back on intraday, which pays off on the likelier windy day, when intraday is cheaper than day-ahead. The risk-averse plan does the opposite at steps 0 to 2: it buys on day-ahead and sells the surplus on intraday. That earns money on a calm day, when intraday pays more than day-ahead, and costs money on a windy day, when it pays less. The plan gives up some of the windy day's profit to lift the calm day's.

## Fields

An `Objective` holds a tuple of `terms`: a `ProfitTerm` is required, a `CVaRTerm` is optional, and each type appears at most once, or building it raises an `OdysValidationError`. The default, `Objective()`, is `Objective(terms=(ProfitTerm(weight=1.0),))`: the expected profit alone. Read a term back with `objective.term_of(CVaRTerm)`.

| Term         | Field              | Type    | Description                                                                 |
| ------------ | ------------------ | ------- | --------------------------------------------------------------------------- |
| `ProfitTerm` | `weight`           | `float` | Weight of the expected profit, at least 0                                   |
| `CVaRTerm`   | `weight`           | `float` | Weight of the CVaR, at least 0                                              |
| `CVaRTerm`   | `confidence_level` | `float` | Share of probability left out of the tail, between 0 and 1 (exclusive)      |

## Choosing the confidence level and the weight

**The confidence level sets which futures count as bad.** At 0.9, the CVaR averages the worst 10 % of probability; at 0.95, the worst 5 %. With few scenarios, that tail is just the worst one: here the calm day alone holds 30 % of the probability, so at any level above 0.7 the CVaR is the calm day's profit.

**The weight sets how much the bad futures count.** Only the ratio of the two weights changes the plan: `ProfitTerm(weight=1.0)` with `CVaRTerm(weight=0.5)` plans like `2.0` with `1.0`. The weights don't have to add up to 1. A higher CVaR weight buys more protection for the bad days, at the cost of the average. With the profit weight at 0, only the bad days count, and the plan for the other scenarios can be any feasible one.

See [Conditional value at risk](../../formulation/objective.md#conditional-value-at-risk) and [CV-1](../../formulation/objective.md#cv-1) for the definition, and the [combined objective](../../formulation/objective.md#combined-objective) for how the weights enter.

## Results

With a risk term, `result.objective_value` is the weighted sum of the expected profit and the CVaR. It ranks plans, but it isn't a profit you can book:

```python
print(round(averse_result.objective_value, 2))
```

```text
-72.2
```

The risk term adds no binaries: one threshold, plus one shortfall per scenario.

## Next steps

The [Day-Ahead or Intraday example](../../examples/day_ahead_or_intraday.md) works through trading under price risk, from the scenarios to the hedged plan, and the [Examples](../../examples/index.md) solve full problems end to end.
