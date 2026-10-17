---
icon: fontawesome/solid/chart-line
---

# EnergyMarket

An `EnergyMarket` represents an electricity market where your portfolio can buy and/or sell energy. Use it to earn revenue from excess generation, or to buy power when it's cheaper than running your own assets.

The optimizer decides how much to buy or sell in each market at every timestep. Markets are not assets: pass them to `EnergySystem(markets=...)`, not to the [AssetPortfolio](../concepts/asset_portfolio.md).

## Basic usage

Let's connect the site of the [running example](../index.md#the-running-example) to a day-ahead market.

```python
from odys import EnergyMarket

day_ahead = EnergyMarket(
    name="day_ahead",
    max_trading_volume_per_step=150.0,
)
```

By default, the market allows either buying or selling up to the specified volume per timestep, but never both in the same timestep.

## Fields

| Field                         | Type                    | Required | Default        | Description                                                                         |
| ----------------------------- | ----------------------- | -------- | -------------- | ----------------------------------------------------------------------------------- |
| `name`                        | `str`                   | Yes      | -              | Unique identifier for the market                                                    |
| `max_trading_volume_per_step` | `float`                 | Yes      | -              | Maximum power bought or sold at each timestep (MW); the energy is this times the step length |
| `allowed_trade_direction`     | `AllowedTradeDirection` | No       | `BUY_AND_SELL` | Allowed directions: `BUY_ONLY`, `SELL_ONLY`, or `BUY_AND_SELL`                      |
| `stage_fixed`                 | `bool`                  | No       | `False`        | If `True`, trading decisions are the same in every scenario                         |

## Trade direction

You can restrict which way the market trades. Use `BUY_ONLY` for procurement markets, `SELL_ONLY` for feed-in tariffs, or leave the default `BUY_AND_SELL` for markets that allow two-way trading.

```python
from odys import AllowedTradeDirection

# Can only sell into this market
feed_in = EnergyMarket(
    name="feed_in",
    max_trading_volume_per_step=100.0,
    allowed_trade_direction=AllowedTradeDirection.SELL_ONLY,
)

# Can only buy from this market
backup_supply = EnergyMarket(
    name="backup_supply",
    max_trading_volume_per_step=50.0,
    allowed_trade_direction=AllowedTradeDirection.BUY_ONLY,
)
```

See the [formulation](#math-trade-direction).

## Stage-fixed decisions

When `stage_fixed=True`, the optimizer must commit to the same trading volumes in every [scenario](../concepts/scenario.md#multiple-scenarios). This models markets where you lock in your position before uncertainty is resolved, like a day-ahead market where bids are placed before you know the actual wind output. Markets you can still trade in once the uncertainty is resolved, like intraday, keep the default and adapt per scenario.

```python
day_ahead = EnergyMarket(
    name="day_ahead",
    max_trading_volume_per_step=150.0,
    stage_fixed=True,  # same volumes in all scenarios
)
```

With a single scenario, `stage_fixed` changes nothing. See [Stochastic optimization](../optimization/stochastic.md#what-is-decided-before-and-after-the-uncertainty) for how it shapes a stochastic run.

See the [formulation](#math-stage-fixed).

## Multiple markets

Pass several markets as a list or tuple, for example the day-ahead market and an intraday market with less liquidity:

```python
intraday = EnergyMarket(name="intraday", max_trading_volume_per_step=50.0)

markets = [day_ahead, intraday]  # EnergySystem(markets=markets, ...)
```

Each market needs its own `PriceProfile`, and the optimizer trades in whichever pays best at each step.

## Profiles

Prices are provided as `PriceProfile` objects in each `Scenario`, not on the market object itself, because they change from one scenario to the next while the market's rules don't:

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

Every market passed to the `EnergySystem` needs a `PriceProfile` in every scenario. Prices are in currency per MWh.

See the [formulation](#math-objective).

## Results

Let's put the whole running example together: the CCGT, the wind farm, the battery, the factory and the flexible process, trading in the day-ahead market. We read the market results through `result.markets`:

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

day_ahead = EnergyMarket(name="day_ahead", max_trading_volume_per_step=150.0)
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

`sell_volume` and `buy_volume` are in MW, and `net_volume` is sell minus buy, so it is negative when the site buys. Each is a `pandas.Series` indexed by market and time (and scenario, when there is more than one).

Notice how the price now drives every asset (print `result.generators`, `result.stationary_storages` and `result.flexible_loads` the same way to see it):

- At 40 and 30 $/MWh (steps 0 and 2), buying is cheaper than the CCGT's 50 $/MWh. The CCGT stays off, the site buys, and the battery charges.
- At 75 and 65 $/MWh (steps 1 and 3), the CCGT runs at full output, the battery discharges, and the surplus is sold.
- At those steps the price is also above the process's 60 $/MWh value of consumption, so the process drops 10 MW below its base and that power is sold instead.

See the [Market Arbitrage example](../../examples/market_arbitrage.md) for buying from a market instead of running a CCGT, and the [CVaR Market Risk example](../../examples/cvar_market_risk.md) for trading under price uncertainty.

## Mathematical formulation

### Variables

| Symbol | Result attribute | Domain | Meaning |
| ------ | ---------------- | ------ | ------- |
| $v^{sell}_{m,t,s}$ | `sell_volume` | $\ge 0$ | Volume sold |
| $v^{buy}_{m,t,s}$ | `buy_volume` | $\ge 0$ | Volume bought |
| $z_{m,t,s}$ | - | $\{0,1\}$ | Trade mode, 1 when selling |

`net_volume` is $v^{sell}_{m,t,s} - v^{buy}_{m,t,s}$.

### Constraints

#### Volume limits and exclusivity {#math-volume}

$$
v^{sell}_{m,t,s} \le V^{\max}_m, \qquad v^{buy}_{m,t,s} \le V^{\max}_m
$$

$$
v^{sell}_{m,t,s} \le z_{m,t,s} \, V^{\max}_m, \qquad
v^{buy}_{m,t,s} \le \left(1 - z_{m,t,s}\right) V^{\max}_m
$$

The binary $z_{m,t,s}$ keeps the market from buying and selling in the same timestep.

#### Trade direction {#math-trade-direction}

$$
v^{sell}_{m,t,s} = 0 \;\text{ if } m \text{ is buy-only}, \qquad
v^{buy}_{m,t,s} = 0 \;\text{ if } m \text{ is sell-only}
$$

#### Stage-fixed decisions {#math-stage-fixed}

For stage-fixed markets, every market variable $x \in \{v^{sell}, v^{buy}, z\}$ takes its first-scenario value in all scenarios:

$$
x_{m,t,s} = x_{m,t,s_0} \quad \forall s
$$

### Objective contribution {#math-objective}

Trading revenue is added to the profit $\Pi_s$:

$$
+ \sum_{t,m} \lambda_{m,t,s} \, \Delta t \left(v^{sell}_{m,t,s} - v^{buy}_{m,t,s}\right)
$$

### Power balance contribution

Buying is supply ($+\sum_m v^{buy}_{m,t,s}$) and selling is demand ($\sum_m v^{sell}_{m,t,s}$). See [Power balance](../concepts/power_balance.md).

## Next steps

See [Objective](../optimization/objective.md) to learn how the market revenue and every asset's costs combine into what the optimizer maximizes.
