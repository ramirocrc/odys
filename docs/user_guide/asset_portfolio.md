---
icon: lucide/briefcase
---

# AssetPortfolio

An `AssetPortfolio` is the container that holds all your energy assets. Let's add generators, storages, loads, EVs, and chargers to it, then pass it to the `EnergySystem`.

We use a separate portfolio object because it keeps asset management clean. You can build the portfolio incrementally, validate names, and query by type, all before creating the `EnergySystem`.

## Basic usage

```python
from odys import AssetPortfolio, FixedLoad, Generator, StationaryStorage

portfolio = AssetPortfolio([
    Generator(name="gen", nominal_power=100.0, variable_cost=50.0),
    StationaryStorage(
        name="bess",
        capacity=50.0,
        max_charge_power=25.0,
        max_discharge_power=25.0,
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

Use `assets_of` with the asset class you want:

```python
from odys import FixedLoad, FlexibleLoad, Generator

portfolio.assets_of(Generator)  # tuple of all Generator assets
portfolio.assets_of(FixedLoad) + portfolio.assets_of(FlexibleLoad)  # all loads
```

It returns a tuple in the order you added the assets, so it's safe to iterate over without worrying about accidental modification.

## Only assets belong in a portfolio

A portfolio holds what you own and operate: generators, storage, electric vehicles, chargers, and loads. Every one of them is an `Asset`. Markets are not assets, so pass them to `EnergySystem(markets=...)`. Putting a market in a portfolio raises an `OdysValidationError`.

## Next steps

Ready to describe the operating conditions? See [Scenario](scenario.md) to define load profiles, generator availability, and market prices.
