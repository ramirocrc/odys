---
icon: lucide/check-circle
---

# `odys.domain.validation`

System-level validation rules. They run automatically when an `EnergySystem` is created, and check that every profile references an entity of the system, every load and market has its required profile in every scenario, every profile fits the horizon, and supply can meet demand. The rules treat entities alike through their capability queries (`max_supply`, `min_demand`, `max_energy_supply`, `validate_horizon`), so a new asset type only needs to override them and be listed as supported. Rules about a single entity or profile run when that object is built.

::: odys.domain.validation
