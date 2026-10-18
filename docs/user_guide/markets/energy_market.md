---
icon: fontawesome/solid/chart-line
---

# EnergyMarket

An `EnergyMarket` models a market your portfolio trades on: a day-ahead or intraday market, a supply contract you buy from, or an offtake agreement you sell to. At every step the optimizer decides how much to buy or sell on it, at the price of that step. Your trades never move the price.

Markets aren't assets. Pass them to the `EnergySystem` with `markets=...`, not to the [AssetPortfolio](../model/first_model.md#the-portfolio).

## Basic usage

Let's connect the site of the [running example](../index.md#the-running-example) to a day-ahead market, trading up to 150 MW per step:

```python
from odys import EnergyMarket

day_ahead = EnergyMarket(
    name="day_ahead",
    max_trading_volume_per_step=150.0,
)
```

By default, a market can buy and sell, but goes only one way at each step: in a given step you either buy from it or sell to it ([M-2](../../formulation/markets.md#m-2)).

## Fields

| Field                         | Type                    | Required | Default        | Description                                                                         |
| ----------------------------- | ----------------------- | -------- | -------------- | ----------------------------------------------------------------------------------- |
| `name`                        | `str`                   | Yes      | -              | Unique name of the market                                                           |
| `max_trading_volume_per_step` | `float`                 | Yes      | -              | Most power bought or sold at each step, above 0 (MW); the energy is this times the step length |
| `allowed_trade_direction`     | `AllowedTradeDirection` | No       | `BUY_AND_SELL` | Which way it trades: `BUY_ONLY`, `SELL_ONLY` or `BUY_AND_SELL`                      |
| `stage_fixed`                 | `bool`                  | No       | `False`        | If `True`, the trades are the same in every scenario                                |

## Volume limit

`max_trading_volume_per_step` is your limit, not the market's: how much you're willing or able to trade per step, such as the rating of your grid connection or the most you'd bid. Set it to what you'd really trade, because the optimizer uses all of it when the price is right.

The limit is a power, in MW, held for the whole step: with 15-minute steps, a 100 MW limit trades at most 25 MWh per step. See [M-1](../../formulation/markets.md#m-1).

## Trade direction

Not every market works both ways. Use `BUY_ONLY` for a supply contract you draw from but can't feed back into, and `SELL_ONLY` for a feed-in tariff or an offtake agreement that buys your output and sells you nothing:

```python
from odys import AllowedTradeDirection

feed_in = EnergyMarket(
    name="feed_in",
    max_trading_volume_per_step=100.0,
    allowed_trade_direction=AllowedTradeDirection.SELL_ONLY,
)

backup_supply = EnergyMarket(
    name="backup_supply",
    max_trading_volume_per_step=50.0,
    allowed_trade_direction=AllowedTradeDirection.BUY_ONLY,
)
```

See [M-3](../../formulation/markets.md#m-3).

## Multiple markets

Pass several markets as a list or tuple, for example the day-ahead market and a thinner intraday market:

```python
intraday = EnergyMarket(name="intraday", max_trading_volume_per_step=50.0)

markets = [day_ahead, intraday]  # EnergySystem(markets=markets, ...)
```

Each market has its own price, and the optimizer trades on whichever pays best at each step. When two markets have different prices at the same step, it also buys on the cheaper one and sells on the dearer one, up to the smaller of the two limits. If that isn't a trade you'd make, set the limits to what you'd really trade, or make one of the markets one-way. See [M-1](../../formulation/markets.md#m-1).

## Stage-fixed markets

Some markets clear before you know which future happens. You place day-ahead bids before you know tomorrow's wind, and you're held to them whatever the wind does. Mark such a market with `stage_fixed=True`, and the optimizer commits to the same trades, and the same direction, in every [scenario](../optimization/stochastic.md#multiple-scenarios):

```python
day_ahead_bids = EnergyMarket(
    name="day_ahead",
    max_trading_volume_per_step=150.0,
    stage_fixed=True,  # one set of bids for every scenario
)
```

A market you can still trade on once the uncertainty is resolved, like intraday, keeps the default and adapts in each scenario. With a single scenario, `stage_fixed` changes nothing. See [Stochastic optimization](../optimization/stochastic.md#what-is-decided-before-and-after-the-uncertainty) for how it shapes a stochastic run, and [NA-1](../../formulation/non_anticipativity.md#na-1).

## Profiles

Prices live in each `Scenario`, as a `PriceProfile`, not on the market, because they change from one future to the next while the market's rules don't. Every market needs a `PriceProfile` in every scenario, in currency per MWh:

```python
from odys import FixedLoad, LoadProfile, PriceProfile, Scenario

factory = FixedLoad(name="factory")

scenario = Scenario(
    profiles=(
        LoadProfile(load=factory, values=[60, 90, 40, 70]),
        PriceProfile(market=day_ahead, values=[40, 75, 30, 65]),
        PriceProfile(market=intraday, values=[45, 80, 25, 65]),
    ),
)
```

The same price applies to buying and selling. Prices can be negative: then selling costs money and buying earns it, so the optimizer may buy just to get paid, as long as something on the site can absorb the power: a battery charging, a flexible load raising its demand, or a generator turning down. See the [objective contribution](../../formulation/markets.md#objective-contribution).

## Results

The market is the last piece of the site. Let's put the whole running example together: the CCGT, the wind farm, the battery, the factory and the flexible process, trading on the day-ahead market:

```python
from datetime import timedelta

from odys import (
    AssetPortfolio,
    AvailableCapacityProfile,
    Battery,
    EnergySystem,
    FlexibleLoad,
    Generator,
    StationaryStorage,
    StorageInitialState,
)

ccgt = Generator(name="ccgt", nominal_power=100.0, variable_cost=50.0)
wind = Generator(name="wind", nominal_power=80.0, variable_cost=0.0)
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

energy_system = EnergySystem(
    portfolio=AssetPortfolio([ccgt, wind, bess, factory, process]),
    markets=day_ahead,
    scenarios=Scenario(
        profiles=(
            LoadProfile(load=factory, values=[60, 90, 40, 70]),
            LoadProfile(load=process, values=[30, 30, 30, 30]),
            AvailableCapacityProfile(generator=wind, values=[40, 10, 60, 30]),
            PriceProfile(market=day_ahead, values=[40, 75, 30, 65]),
        ),
    ),
    timestep=timedelta(hours=1),
    number_of_steps=4,
    initial_conditions=(StorageInitialState(storage=bess, soc=0.5),),
)

result = energy_system.optimize()
print(result.markets.to_dataframe().round(2))
```

```text
                sell_volume  buy_volume  net_volume
time market
0    day_ahead          0.0       74.09      -74.09
1    day_ahead         25.0        0.00       25.00
2    day_ahead          0.0       55.00      -55.00
3    day_ahead         65.0        0.00       65.00
```

The price now drives every asset. Print `result.generators`, `result.stationary_storages` and `result.flexible_loads` the same way to see it:

- **Steps 0 and 2, at 40 and 30 $/MWh:** buying is cheaper than the CCGT's 50 $/MWh, so the CCGT stays off and the site buys. The battery charges, and the process takes its full 20 MW extra, because power costs less than the 60 $/MWh its consumption is worth.
- **Steps 1 and 3, at 75 and 65 $/MWh:** the CCGT runs at full output, the battery discharges at 25 MW, and the process cuts 10 MW, because the power is worth more on the market. The surplus is sold.

The battery only tops up at step 0: half full, it already holds nearly enough for step 1. It ends the day empty, because nothing asks it to keep a charge (see [State of charge](../assets/battery.md#state-of-charge)).

The market's results are in `result.markets`, one `pandas.Series` per series, indexed by market and time, and by scenario when there's more than one:

- `buy_volume` and `sell_volume`: the power bought and sold, in MW.
- `net_volume`: sell minus buy, so negative when the site buys.

The [Market Arbitrage example](../../examples/market_arbitrage.md) buys from a market instead of running a CCGT, and the [CVaR Market Risk example](../../examples/cvar_market_risk.md) trades under price uncertainty.

## How it's modelled

A market has a buy volume, a sell volume and a trade mode at every step, in every scenario. The rules are on the [Markets](../../formulation/markets.md) formulation page: the volume limit ([M-1](../../formulation/markets.md#m-1)), one direction per step ([M-2](../../formulation/markets.md#m-2)) and one-way markets ([M-3](../../formulation/markets.md#m-3)). Stage-fixed markets add [NA-1](../../formulation/non_anticipativity.md#na-1). Buying supplies the [power balance](../../formulation/power_balance.md#pb-1) and selling draws from it, and the trading revenue enters the [objective](../../formulation/markets.md#objective-contribution).

## Next steps

The site is complete. Next, see how to read everything the optimizer decided, in [Results](../solving/results.md).
