# Markets + Stochastic

This example combines stochastic scenarios with multiple electricity markets, including stage-fixed decisions. It's the most complete example in the collection.

**Source**: [`examples/example5.py`](https://github.com/ramirocrc/odys/blob/main/examples/example5.py)

## What it demonstrates

- Stochastic scenarios with different market prices per scenario
- `stage_fixed=True` on the day-ahead market (same volumes in all scenarios)
- `TradeDirection.BUY` to restrict markets to buy-only
- How the optimizer splits decisions between "commit now" and "adjust later"

## The setup

Two generators, a fixed load, and three buy-only markets:

- **sdac**: Day-ahead market, `stage_fixed=True` -- bids must be identical across scenarios
- **sidc1**: Intraday market 1 -- can adjust per scenario
- **sidc2**: Intraday market 2 -- can adjust per scenario

Two scenarios with different price forecasts.

## Code

```python
from datetime import timedelta

from odys.energy_system import EnergySystem
from odys.energy_system_models.assets.generator import PowerGenerator
from odys.energy_system_models.assets.load import Load, LoadType
from odys.energy_system_models.assets.portfolio import AssetPortfolio
from odys.energy_system_models.markets import EnergyMarket, TradeDirection
from odys.energy_system_models.scenarios import StochasticScenario

generator_1 = PowerGenerator(
    name="gen1",
    nominal_power=100.0,
    variable_cost=20.0,
    min_up_time=1,
    ramp_down=100,
)
generator_2 = PowerGenerator(
    name="gen2",
    nominal_power=150.0,
    variable_cost=100.0,
    min_up_time=4,
    min_power=30,
    startup_cost=0,
    ramp_up=140,
    ramp_down=100,
)

portfolio = AssetPortfolio()
portfolio.add_asset(generator_1)
portfolio.add_asset(generator_2)
portfolio.add_asset(Load(name="load", type=LoadType.Fixed))

energy_system = EnergySystem(
    portfolio=portfolio,
    markets=(
        EnergyMarket(
            name="sdac",
            max_trading_volume_per_step=150,
            stage_fixed=True,
            trade_direction=TradeDirection.BUY,
        ),
        EnergyMarket(
            name="sidc1",
            max_trading_volume_per_step=100,
            trade_direction=TradeDirection.BUY,
        ),
        EnergyMarket(
            name="sidc2",
            max_trading_volume_per_step=50,
            trade_direction=TradeDirection.BUY,
        ),
    ),
    scenarios=[
        StochasticScenario(
            name="scenario1",
            probability=0.5,
            available_capacity_profiles={
                "gen1": [100, 100, 100, 50, 50, 50, 50],
            },
            load_profiles={"load": [200, 75, 200, 50, 100, 120, 125]},
            market_prices={
                "sdac": [150, 150, 150, 150, 150, 150, 150],
                "sidc1": [200, 200, 200, 175, 100, 100, 100],
                "sidc2": [190, 150, 150, 175, 100, 100, 100],
            },
        ),
        StochasticScenario(
            name="scenario2",
            probability=0.5,
            available_capacity_profiles={
                "gen1": [100, 100, 100, 50, 50, 50, 50],
            },
            load_profiles={"load": [200, 75, 200, 50, 100, 120, 125]},
            market_prices={
                "sdac": [210, 210, 210, 185, 100, 100, 100],
                "sidc1": [120, 140, 140, 140, 140, 140, 140],
                "sidc2": [200, 160, 140, 180, 110, 90, 100],
            },
        ),
    ],
    timestep=timedelta(minutes=30),
    number_of_steps=7,
    power_unit="MW",
)

result = energy_system.optimize()
```

## Reading the results

```python
print(result.generators.power)     # dispatch per scenario
print(result.markets.sell_volume)   # (should be zero -- buy-only markets)
print(result.markets.buy_volume)    # volumes bought from each market
print(result.to_dataframe)
```

## What to look for

- The **sdac** buy volumes are identical in both scenarios because `stage_fixed=True`. The optimizer picks volumes that work well on average.
- **sidc1** and **sidc2** volumes differ between scenarios since the optimizer can react to the realized prices.
- All markets are buy-only (`TradeDirection.BUY`), so `sell_volume` should be zero.
- Compare the sdac volumes across scenarios -- they're the same, which is the non-anticipativity constraint at work.
