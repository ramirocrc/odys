# Markets

This example shows how to include electricity markets in a deterministic dispatch problem. Generators can sell excess power into markets for additional revenue.

**Source**: [`examples/example4.py`](https://github.com/ramirocrc/odys/blob/main/examples/example4.py)

## What it demonstrates

- Adding multiple `EnergyMarket` instances with different volume limits
- Providing `market_prices` in the scenario
- How the optimizer decides where to sell excess generation

## The setup

Two generators with different costs, a fixed load, and three electricity markets:

- **sdac**: Day-ahead market (max 150 MW/step)
- **sidc1**: Intraday market 1 (max 100 MW/step)
- **sidc2**: Intraday market 2 (max 50 MW/step)

Each market has its own price timeseries. The optimizer will dispatch generators to meet the load and then sell any excess into the most profitable market.

## Code

```python
from datetime import timedelta

from odys.energy_system import EnergySystem
from odys.energy_system_models.assets.generator import PowerGenerator
from odys.energy_system_models.assets.load import Load, LoadType
from odys.energy_system_models.assets.portfolio import AssetPortfolio
from odys.energy_system_models.markets import EnergyMarket
from odys.energy_system_models.scenarios import Scenario

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
        EnergyMarket(name="sdac", max_trading_volume_per_step=150),
        EnergyMarket(name="sidc1", max_trading_volume_per_step=100),
        EnergyMarket(name="sidc2", max_trading_volume_per_step=50),
    ),
    scenarios=Scenario(
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
    timestep=timedelta(minutes=30),
    number_of_steps=7,
    power_unit="MW",
)

result = energy_system.optimize()
```

## Reading the results

```python
print(result.generators.power)     # how much each generator produces
print(result.markets.sell_volume)   # how much is sold to each market
print(result.to_dataframe)          # everything in one place
```

## What to look for

- The optimizer sells excess generation to whichever market pays the most at each timestep.
- **sidc1** has higher prices than **sdac** in the first few steps, so it gets filled first (up to its volume limit).
- Generators may produce more than the load requires when market revenue exceeds operating costs.
