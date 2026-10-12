---
icon: lucide/table
---

# Results

`energy_system.optimize()` returns an `OptimalDispatchResults` object with the solver status and one results container per asset type.

## Basic usage

```python
result = energy_system.optimize()

result.generators.to_dataframe()
```

## Solver status

```python
result.solver_status  # SolveStatus.OK ("ok") if the solver found a solution
result.termination_condition  # "optimal" if it's the best possible solution
result.objective_value  # objective value of the solved model
```

## Results containers

Each asset type and the markets have their own container. Its attributes are listed on the linked page:

| Container | Attributes | Details |
| --------- | ---------- | ------- |
| `result.generators` | `power`, `status`, `startup`, `shutdown` | [Generator](../assets/generator.md#results) |
| `result.flexible_loads` | `load_adjustment`, `actual_load` | [FlexibleLoad](../assets/flexible_load.md#results) |
| `result.stationary_storages` | `net_power`, `soc`, `charge_mode` | [StationaryStorage](../assets/stationary_storage.md#results) |
| `result.electric_vehicles` | `net_power`, `soc`, `charge_mode` | [ElectricVehicle](../assets/electric_vehicle.md#results) |
| `result.chargers` | `assignment`, `power` | [Charger](../assets/charger.md#results) |
| `result.markets` | `sell_volume`, `buy_volume`, `net_volume` | [EnergyMarket](../markets/energy_market.md#results) |

Fixed loads have no decisions, so they have no container.

## Data formats

All of these attributes are `pandas.Series` objects, indexed by entity and time (and scenario, when there is more than one). Each container also exposes `.to_dataframe()` and `.to_dataset()`:

```python
result.generators.to_dataframe()
result.stationary_storages.to_dataset()
```

For the full raw solution as an xarray Dataset:

```python
result.to_dataset()
```

!!! tip

    If you're working in a notebook, `result.generators.to_dataframe()` is usually the quickest way to see what the optimizer did. You can export it with `.to_csv()` or plot it directly.

## Next steps

Want to switch solvers or tune solver options? See [Solvers](solvers.md) to configure the optimization backend.
