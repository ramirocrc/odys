# AssetPortfolio

An `AssetPortfolio` is the container that holds all your energy assets. You add generators, batteries, and loads to it, then pass it to the `EnergySystem`.

## Basic usage

```python
from odys.energy_system_models.assets.generator import PowerGenerator
from odys.energy_system_models.assets.load import Load
from odys.energy_system_models.assets.portfolio import AssetPortfolio
from odys.energy_system_models.assets.storage import Battery

portfolio = AssetPortfolio()
portfolio.add_asset(PowerGenerator(name="gen", nominal_power=100.0, variable_cost=50.0))
portfolio.add_asset(Battery(
    name="bess", capacity=50.0, max_power=25.0,
    efficiency_charging=0.95, efficiency_discharging=0.95, soc_start=0.5,
))
portfolio.add_asset(Load(name="demand"))
```

## Adding assets

Use `add_asset()` to add any `EnergyAsset` (generators, batteries, loads):

```python
portfolio = AssetPortfolio()
portfolio.add_asset(generator)
portfolio.add_asset(battery)
portfolio.add_asset(load)
```

!!! warning
    Asset names must be unique within a portfolio. Adding two assets with the same `name` raises a `ValueError`.

## Accessing assets

You can retrieve a specific asset by name:

```python
gen = portfolio.get_asset("gen")
```

Or get a read-only view of all assets:

```python
all_assets = portfolio.assets  # MappingProxyType (read-only dict)
```

## Filtering by type

The portfolio has convenience properties to get assets by type:

```python
portfolio.generators  # tuple of all PowerGenerator assets
portfolio.batteries   # tuple of all Battery assets
portfolio.loads       # tuple of all Load assets
```

These return tuples, so they're safe to iterate over without worrying about accidental modification.
