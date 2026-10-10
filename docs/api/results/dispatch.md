---
icon: lucide/arrow-right
---

# `odys.results.dispatch`

Typed dispatch result containers: `GeneratorDispatch`, `StationaryStorageDispatch`, `ElectricVehicleDispatch`, `ChargerDispatch`, `MarketDispatch`, and `FlexibleLoadDispatch`. Each is a `Dispatch` (storage and electric vehicles through `BatteryDispatch`): select one entity with `dispatch["name"]`, iterate over the entities, read each series as a `pandas.Series` property, or get everything with `.to_dataframe()` and `.to_dataset()`.

See [Reading results](../../user_guide/optimization.md#reading-results) in the User Guide.

::: odys.results.dispatch
