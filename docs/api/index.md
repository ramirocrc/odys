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
- `odys.utils`

## Package tree

- `odys`
- `odys.domain`
  - `odys.domain.entities`
    - `odys.domain.entities.base`
    - `odys.domain.entities.charger`
    - `odys.domain.entities.electric_vehicle`
    - `odys.domain.entities.fixed_load`
    - `odys.domain.entities.flexible_load`
    - `odys.domain.entities.generator`
    - `odys.domain.entities.market`
    - `odys.domain.entities.portfolio`
    - `odys.domain.entities.standalone_storage`
    - `odys.domain.entities.storage`
    - `odys.domain.entities.trip`
  - `odys.domain.exceptions`
  - `odys.domain.objective`
  - `odys.domain.scenarios`
  - `odys.domain.validation`
- `odys.energy_system`
- `odys.optimization`
  - `odys.optimization.constraints`
    - `odys.optimization.constraints.charger_constraints`
    - `odys.optimization.constraints.constraints_group`
    - `odys.optimization.constraints.cvar_constraints`
    - `odys.optimization.constraints.electric_vehicle_constraints`
    - `odys.optimization.constraints.flexible_load_constraints`
    - `odys.optimization.constraints.generator_constraints`
    - `odys.optimization.constraints.market_constraints`
    - `odys.optimization.constraints.model_constraint`
    - `odys.optimization.constraints.scenario_constraints`
    - `odys.optimization.constraints.standalone_storage_constraints`
    - `odys.optimization.constraints.storage_constraints`
  - `odys.optimization.model`
    - `odys.optimization.model.dimensions`
    - `odys.optimization.model.indices`
    - `odys.optimization.model.linopy_converter`
    - `odys.optimization.model.milp_model`
    - `odys.optimization.model.model_builder`
    - `odys.optimization.model.objectives`
    - `odys.optimization.model.registry`
    - `odys.optimization.model.variable_definitions`
  - `odys.optimization.parameters`
    - `odys.optimization.parameters.energy_system_parameters`
    - `odys.optimization.parameters.entity_parameters`
      - `odys.optimization.parameters.entity_parameters.charger_parameters`
      - `odys.optimization.parameters.entity_parameters.electric_vehicle_parameters`
      - `odys.optimization.parameters.entity_parameters.flexible_load_parameters`
      - `odys.optimization.parameters.entity_parameters.generator_parameters`
      - `odys.optimization.parameters.entity_parameters.market_parameters`
      - `odys.optimization.parameters.entity_parameters.scenario_parameters`
      - `odys.optimization.parameters.entity_parameters.standalone_storage_parameters`
- `odys.results`
  - `odys.results.dispatch`
  - `odys.results.optimization_results`
- `odys.solvers`
  - `odys.solvers.config_translators`
  - `odys.solvers.solver`
  - `odys.solvers.solver_config`
- `odys.utils`
  - `odys.utils.logging`
