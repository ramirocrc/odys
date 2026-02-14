# Market

An `EnergyMarket` represents an electricity market where your portfolio can buy and/or sell energy. This is how you model revenue from selling excess generation or purchasing power when it's cheaper than running your own assets.

## Basic usage

```python
from odys.energy_system_models.markets import EnergyMarket

market = EnergyMarket(
    name="day_ahead",
    max_trading_volume_per_step=150.0,
)
```

By default, the market allows both buying and selling up to the specified volume per timestep.

## Fields

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `name` | `str` | Yes | - | Unique identifier for the market |
| `max_trading_volume_per_step` | `float` | Yes | - | Maximum volume that can be traded per timestep (MW) |
| `trade_direction` | `TradeDirection` | No | `"both"` | Allowed trade directions: `"buy"`, `"sell"`, or `"both"` |
| `stage_fixed` | `bool` | No | `False` | If `True`, trading decisions are fixed across all scenarios |

## Trade direction

You can restrict which way the market trades:

```python
from odys.energy_system_models.markets import EnergyMarket, TradeDirection

# Can only sell into this market
sell_only = EnergyMarket(
    name="feed_in",
    max_trading_volume_per_step=100.0,
    trade_direction=TradeDirection.SELL,
)

# Can only buy from this market
buy_only = EnergyMarket(
    name="backup_supply",
    max_trading_volume_per_step=50.0,
    trade_direction=TradeDirection.BUY,
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

## Market prices

Prices are provided through the `Scenario` (or `StochasticScenario`), not on the market object itself:

```python
from odys.energy_system_models.scenarios import Scenario

scenario = Scenario(
    market_prices={
        "day_ahead": [50, 55, 45, 60, 70, 65, 50],
    },
    load_profiles={"load": [100, 120, 80, 90, 110, 100, 95]},
)
```

The key must match the market's `name`.

## Multiple markets

You can pass multiple markets to the `EnergySystem`:

```python
from odys.energy_system import EnergySystem

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
    power_unit="MW",
)
```

## Results

After optimization, access market results through `result.markets`:

```python
result = energy_system.optimize()

result.markets.sell_volume  # energy sold per market per timestep
result.markets.buy_volume   # energy bought per market per timestep
```

Each of these is a `pandas.DataFrame`.
