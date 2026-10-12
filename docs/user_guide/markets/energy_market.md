---
icon: fontawesome/solid/chart-line
---

# EnergyMarket

An `EnergyMarket` represents an electricity market where your portfolio can buy and/or sell energy. Use this to model revenue from selling excess generation or purchasing power when it's cheaper than running your own assets.

Markets are not assets: pass them to `EnergySystem(markets=...)`, not to the [AssetPortfolio](../concepts/asset_portfolio.md).

## Basic usage

Let's create a market.

```python
from odys import EnergyMarket

market = EnergyMarket(
    name="day_ahead",
    max_trading_volume_per_step=150.0,
)
```

By default, the market allows either buying or selling up to the specified volume per timestep, but never both in the same timestep.

## Fields

| Field                         | Type                    | Required | Default        | Description                                                    |
| ----------------------------- | ----------------------- | -------- | -------------- | -------------------------------------------------------------- |
| `name`                        | `str`                   | Yes      | -              | Unique identifier for the market                               |
| `max_trading_volume_per_step` | `float`                 | Yes      | -              | Maximum volume that can be traded per timestep (MW)            |
| `allowed_trade_direction`     | `AllowedTradeDirection` | No       | `BUY_AND_SELL` | Allowed directions: `BUY_ONLY`, `SELL_ONLY`, or `BUY_AND_SELL` |
| `stage_fixed`                 | `bool`                  | No       | `False`        | If `True`, trading decisions are fixed across all scenarios    |

## Trade direction

You can restrict which way the market trades. Use `BUY_ONLY` for procurement markets, `SELL_ONLY` for feed-in tariffs, or leave the default `BUY_AND_SELL` for markets that allow two-way trading.

```python
from odys import EnergyMarket, AllowedTradeDirection

# Can only sell into this market
sell_only = EnergyMarket(
    name="feed_in",
    max_trading_volume_per_step=100.0,
    allowed_trade_direction=AllowedTradeDirection.SELL_ONLY,
)

# Can only buy from this market
buy_only = EnergyMarket(
    name="backup_supply",
    max_trading_volume_per_step=50.0,
    allowed_trade_direction=AllowedTradeDirection.BUY_ONLY,
)
```

See the [formulation](#math-trade-direction).

## Stage-fixed decisions

When `stage_fixed=True`, the optimizer must commit to the same trading volumes across all stochastic scenarios. This models markets where you need to lock in your position before uncertainty is resolved -- like a day-ahead market where bids are placed before you know the actual wind/solar output.

```python
day_ahead = EnergyMarket(
    name="day_ahead",
    max_trading_volume_per_step=150.0,
    stage_fixed=True,  # same volumes in all scenarios
)

intraday = EnergyMarket(
    name="intraday",
    max_trading_volume_per_step=50.0,
    stage_fixed=False,  # can adjust per scenario (default)
)
```

This is particularly useful in [stochastic optimization](../optimization/stochastic.md) setups.

See the [formulation](#math-stage-fixed).

## Multiple markets

You can pass multiple markets to the `EnergySystem`:

```python
from odys import EnergySystem

energy_system = EnergySystem(
    portfolio=portfolio,
    markets=(
        EnergyMarket(name="sdac", max_trading_volume_per_step=150),
        EnergyMarket(name="sidc1", max_trading_volume_per_step=100),
        EnergyMarket(name="sidc2", max_trading_volume_per_step=50),
    ),
    scenarios=scenario,
    timestep=timedelta(minutes=30),
    number_of_steps=7,
)
```

## Profiles

Prices are provided as `PriceProfile` objects in each `Scenario`, not on the market object itself:

```python
from odys import LoadProfile, FixedLoad, PriceProfile, Scenario

load = FixedLoad(name="load")

scenario = Scenario(
    profiles=(
        PriceProfile(market=day_ahead, values=[50, 55, 45, 60, 70, 65, 50]),
        LoadProfile(load=load, values=[100, 120, 80, 90, 110, 100, 95]),
    ),
)
```

Every market passed to the `EnergySystem` needs a `PriceProfile` in every scenario. Prices are in currency per MWh.

See the [formulation](#math-objective).

## Results

After optimization, access market results through `result.markets`:

```python
result = energy_system.optimize()

result.markets.sell_volume  # energy sold per market per timestep
result.markets.buy_volume  # energy bought per market per timestep
result.markets.net_volume  # sell minus buy
```

Each of these is a `pandas.Series` indexed by market and time (and scenario, when there is more than one).

## Mathematical formulation

See [Mathematical notation](../mathematical_notation.md) for every symbol.

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
