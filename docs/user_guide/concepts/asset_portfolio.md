---
icon: lucide/briefcase
---

# AssetPortfolio

An `AssetPortfolio` is the container that holds all your energy assets: generators, loads, storage, electric vehicles and chargers. You build it once and pass it to the `EnergySystem`.

We use a separate portfolio object because it keeps asset management clean. You can build the portfolio, validate names, and query by type, all before creating the `EnergySystem`.

## Basic usage

Let's collect the two assets of our [first system](energy_system.md#basic-usage):

```python
from odys import AssetPortfolio, FixedLoad, Generator

ccgt = Generator(name="ccgt", nominal_power=100.0, variable_cost=50.0)
factory = FixedLoad(name="factory")

portfolio = AssetPortfolio([ccgt, factory])
```

Pass it to the system with `EnergySystem(portfolio=portfolio, ...)`.

!!! warning

    Asset names must be unique within a portfolio. Adding two assets with the same `name` raises an `OdysValidationError`.

    Chargers and electric vehicles come together: a portfolio with electric vehicles but no charger, or chargers but no electric vehicle, also raises an `OdysValidationError`.

## Accessing assets

Retrieve a specific asset by name:

```python
portfolio.get_asset("ccgt")
```

Or get a read-only view of all assets, keyed by name:

```python
portfolio.assets  # MappingProxyType (read-only dict)
```

## Filtering by type

Use `assets_of` with the asset class you want:

```python
from odys import FixedLoad, FlexibleLoad, Generator

portfolio.assets_of(Generator)  # (ccgt,)
portfolio.assets_of(FixedLoad) + portfolio.assets_of(FlexibleLoad)  # all loads
```

It returns a tuple in the order you added the assets, so it's safe to iterate over without worrying about accidental modification.

## Only assets belong in a portfolio

A portfolio holds what you own and operate: [generators](../assets/generator.md), [fixed](../assets/fixed_load.md) and [flexible](../assets/flexible_load.md) loads, [storage](../assets/stationary_storage.md), [electric vehicles](../assets/electric_vehicle.md) and [chargers](../assets/charger.md). Every one of them is an `Asset`. Markets are not assets, so pass them to `EnergySystem(markets=...)` (see [EnergyMarket](../markets/energy_market.md)). Putting a market in a portfolio raises an `OdysValidationError`.

## Next steps

The portfolio says what you own. Next, [Scenarios & Profiles](scenario.md) describe how it is used over time: demand, generator availability, and market prices.
