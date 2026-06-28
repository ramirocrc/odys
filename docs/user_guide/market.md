---
icon: fontawesome/solid/chart-line
---

# Market

An `EnergyMarket` represents an electricity market where your portfolio can buy and/or sell energy. Use this to model revenue from selling excess generation or purchasing power when it's cheaper than running your own assets.

See [Mathematical notation](mathematical_notation.md) for the full list of symbols used below.

## Basic usage

Let's create a market.

```python
from odys import EnergyMarket

market = EnergyMarket(
    name="day_ahead",
    max_trading_volume_per_step=150.0,
)
```

By default, the market allows either buying or selling up to the specified volume per timestep. The current optimization model prevents buying and selling in the same market at the same timestep.

That means:

$$
0 \le v^{buy}_{m,t} \le V^{\max}_m, \qquad 0 \le v^{sell}_{m,t} \le V^{\max}_m, \qquad z_{m,t} \in \{0,1\}
$$

and mutual exclusivity is enforced as:

$$
v^{sell}_{m,t} \le z_{m,t} V^{\max}_m
$$

$$
v^{buy}_{m,t} + z_{m,t} V^{\max}_m \le V^{\max}_m
$$

## Fields

| Field                         | Type             | Required | Default  | Description                                                 |
| ----------------------------- | ---------------- | -------- | -------- | ----------------------------------------------------------- |
| `name`                        | `str`            | Yes      | -        | Unique identifier for the market                            |
| `max_trading_volume_per_step` | `float`          | Yes      | -        | Maximum volume that can be traded per timestep (MW)         |
| `trade_direction`             | `TradeDirection` | No       | `"both"` | Allowed trade directions: `"buy"`, `"sell"`, or `"both"`    |
| `stage_fixed`                 | `bool`           | No       | `False`  | If `True`, trading decisions are fixed across all scenarios |

## Trade direction

You can restrict which way the market trades. Use `BUY_ONLY` for procurement markets, `SELL_ONLY` for feed-in tariffs, or leave it as `"both"` for markets that allow two-way trading.

```python
from odys import EnergyMarket, TradeDirection

# Can only sell into this market
sell_only = EnergyMarket(
    name="feed_in",
    max_trading_volume_per_step=100.0,
    trade_direction=TradeDirection.SELL_ONLY,
)

# Can only buy from this market
buy_only = EnergyMarket(
    name="backup_supply",
    max_trading_volume_per_step=50.0,
    trade_direction=TradeDirection.BUY_ONLY,
)
```

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

This is particularly useful in [stochastic optimization](stochastic.md) setups.

For stage-fixed markets, the same buy volume, sell volume, and trade mode are enforced across scenarios:

$$
x_{m,t,s} = x_{m,t,s_0} \quad \forall s
$$

## Market prices

Prices are provided through the `Scenario` (or `StochasticScenario`), not on the market object itself:

```python
from odys import Scenario

scenario = Scenario(
    market_prices={
        "day_ahead": [50, 55, 45, 60, 70, 65, 50],
    },
    load_profiles={"load": [100, 120, 80, 90, 110, 100, 95]},
)
```

The key must match the market's `name`.

Revenue and cost enter the objective as:

$$
\sum_{t,m} \lambda_{m,t,s}\left(v^{sell}_{m,t,s} - v^{buy}_{m,t,s}\right)
$$

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

## Results

After optimization, access market results through `result.markets`:

```python
result = energy_system.optimize()

result.markets.sell_volume  # energy sold per market per timestep
result.markets.buy_volume  # energy bought per market per timestep
```

Each of these is a `pandas.DataFrame`.

## Next steps

Now that you understand all the asset types, see [AssetPortfolio](asset_portfolio.md) to learn how to combine them into a single portfolio.
