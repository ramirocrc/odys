---
icon: lucide/briefcase
---

# AssetPortfolio

An `AssetPortfolio` is the container that holds all your energy assets. Let's add generators, storages, and loads to it, then pass it to the `EnergySystem`.

We use a separate portfolio object because it keeps asset management clean. You can build the portfolio incrementally, validate names, and query by type -- all before creating the `EnergySystem`.

## Basic usage

```python
from odys import AssetPortfolio, FixedLoad, Generator, Storage

portfolio = AssetPortfolio([
    Generator(name="gen", nominal_power=100.0, variable_cost=50.0),
    Storage(
        name="bess",
        capacity=50.0,
        max_power=25.0,
        efficiency_charging=0.95,
        efficiency_discharging=0.95,
        soc_start=0.5,
    ),
    FixedLoad(name="demand"),
])
```

## Creating a portfolio

Pass a list of assets to the `AssetPortfolio` constructor:

```python
portfolio = AssetPortfolio([generator, battery, fixed_load, flexible_load])
```

!!! warning

    Asset names must be unique within a portfolio. Adding two assets with the same `name` raises an `OdysValidationError`.

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
portfolio.generators  # tuple of all Generator assets
portfolio.storages  # tuple of all Storage assets
portfolio.fixed_loads  # tuple of all FixedLoad assets
portfolio.flexible_loads  # tuple of all FlexibleLoad assets
```

These return tuples, so they're safe to iterate over without worrying about accidental modification.

## Next steps

Ready to describe the operating conditions? See [Scenario](scenario.md) to define load profiles, generator availability, and market prices.
