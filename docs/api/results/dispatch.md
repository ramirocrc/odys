---
icon: lucide/arrow-right
---

# `odys.results.dispatch`

Typed dispatch result containers: `GeneratorDispatch` (power, status, startup, shutdown), `StorageDispatch` (net power, SOC, charge mode), `MarketDispatch` (buy/sell volume), and `FlexibleLoadDispatch` (load_adjustment, actual_load). All expose `.to_dataframe()` and `.to_dataset()`.

See [Reading results](../../user_guide/optimization.md#reading-results) in the User Guide.

::: odys.results.dispatch
