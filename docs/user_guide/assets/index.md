---
icon: lucide/boxes
---

# Assets

Assets are what you own and operate. You put them in an [AssetPortfolio](../concepts/asset_portfolio.md) and the optimizer decides how to run them. Markets are not assets; see [EnergyMarket](../markets/energy_market.md).

| Asset | Represents | Scenario profile | Power balance | Results |
| ----- | ---------- | ---------------- | ------------- | ------- |
| [Generator](generator.md) | Dispatchable power source | `AvailableCapacityProfile` (optional) | Supply | `result.generators` |
| [FixedLoad](fixed_load.md) | Inelastic demand | `LoadProfile` (required) | Demand | - |
| [FlexibleLoad](flexible_load.md) | Demand that can move up or down | `LoadProfile` (required, base profile) | Demand | `result.flexible_loads` |
| [StationaryStorage](stationary_storage.md) | Battery at a fixed site | - | Supply (discharge) and demand (charge) | `result.stationary_storages` |
| [ElectricVehicle](electric_vehicle.md) | Battery with a trip schedule | - | Supply (V2G) and demand (charge) | `result.electric_vehicles` |
| [Charger](charger.md) | Connection point for EVs | - | None | `result.chargers` |

StationaryStorage and ElectricVehicle both have a [Battery](battery.md), which holds their shared physics.

## How the asset pages are organized

Every asset page follows the same structure:

1. **Basic usage**: the smallest working example.
2. **Fields**: every constructor argument.
3. **Features**: one section per optional behaviour, in plain words with an example.
4. **Profiles**: the time series the asset takes from a [Scenario](../concepts/scenario.md), if any.
5. **Results**: what you can read after `optimize()`.
6. **Mathematical formulation**: variables, constraints, and the asset's contribution to the [objective](../optimization/objective.md) and the [power balance](../concepts/power_balance.md).

Each feature section links to the constraints that implement it, so you can skip the math until you need it.

## Combining assets

You can mix any assets in the same portfolio, for example fixed and flexible loads:

```python
from odys import AssetPortfolio, LoadProfile, FixedLoad, FlexibleLoad, Scenario

fixed_load = FixedLoad(name="critical_demand")
flexible_load = FlexibleLoad(
    name="adjustable_demand",
    max_increase=30.0,
    max_decrease=20.0,
    value_of_consumption=75.0,
)

portfolio = AssetPortfolio([fixed_load, flexible_load])

scenario = Scenario(
    profiles=(
        LoadProfile(load=fixed_load, values=[100, 100, 100, 100]),
        LoadProfile(load=flexible_load, values=[50, 50, 50, 50]),
    ),
)
```

## Next steps

Start with [Generator](generator.md), the simplest asset with decisions to make.
