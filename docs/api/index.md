---
icon: lucide/code
---

# API Reference

Use this section to find the public import surface first, then drill into internals only when you need implementation details.

## Start here

- `odys` for top-level exports and the main import path
- `odys.energy_system` for building and optimizing a system
- `odys.domain` for asset, scenario, and validation models
- `odys.results` for optimization outputs and dispatch data

## Public API

- `odys`
- `odys.energy_system`
- `odys.domain`
- `odys.results`

## Internal reference

- `odys.optimization`
- `odys.solvers`

## Package tree

- `odys`
- `odys.domain`
  - `odys.domain.entities`
    - `odys.domain.entities.base`
    - `odys.domain.entities.battery`
    - `odys.domain.entities.charger`
    - `odys.domain.entities.electric_vehicle`
    - `odys.domain.entities.fixed_load`
    - `odys.domain.entities.flexible_load`
    - `odys.domain.entities.generator`
    - `odys.domain.entities.market`
    - `odys.domain.entities.portfolio`
    - `odys.domain.entities.stationary_storage`
    - `odys.domain.entities.trip`
  - `odys.domain.exceptions`
  - `odys.domain.objective`
  - `odys.domain.profiles`
  - `odys.domain.scenario`
  - `odys.domain.validation`
- `odys.energy_system`
- `odys.optimization`
  - `odys.optimization.constraints`
    - `odys.optimization.constraints.constraints_group`
    - `odys.optimization.constraints.model_constraint`
  - `odys.optimization.formulations`
    - `odys.optimization.formulations.base`
    - `odys.optimization.formulations.charging`
    - `odys.optimization.formulations.electric_vehicle`
    - `odys.optimization.formulations.energy_market`
    - `odys.optimization.formulations.fixed_load`
    - `odys.optimization.formulations.flexible_load`
    - `odys.optimization.formulations.generator`
    - `odys.optimization.formulations.stationary_storage`
    - `odys.optimization.formulations.storage`
  - `odys.optimization.model`
    - `odys.optimization.model.model_builder`
  - `odys.optimization.objective_terms`
    - `odys.optimization.objective_terms.base`
    - `odys.optimization.objective_terms.cvar`
    - `odys.optimization.objective_terms.profit`
  - `odys.optimization.power_balance`
  - `odys.optimization.problem`
  - `odys.optimization.variable_owner`
  - `odys.parameters`
    - `odys.parameters.dimensions`
    - `odys.parameters.coordinates`
    - `odys.parameters.context`
    - `odys.parameters.vectorize`
    - `odys.parameters.entity_arrays`
- `odys.results`
  - `odys.results.dispatch`
  - `odys.results.optimization_results`
- `odys.solvers`
  - `odys.solvers.config_translators`
  - `odys.solvers.solver`
  - `odys.solvers.solver_config`
