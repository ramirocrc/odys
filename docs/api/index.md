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
    - `odys.domain.entities.generator`
    - `odys.domain.entities.load`
    - `odys.domain.entities.market`
    - `odys.domain.entities.portfolio`
    - `odys.domain.entities.storage`
  - `odys.domain.exceptions`
  - `odys.domain.objective`
  - `odys.domain.scenarios`
  - `odys.domain.validation`
- `odys.energy_system`
- `odys.optimization`
  - `odys.optimization.constraints`
    - `odys.optimization.constraints.constraints_group`
    - `odys.optimization.constraints.cvar_constraints`
    - `odys.optimization.constraints.generator_constraints`
    - `odys.optimization.constraints.market_constraints`
    - `odys.optimization.constraints.model_constraint`
    - `odys.optimization.constraints.scenario_constraints`
    - `odys.optimization.constraints.storage_constraints`
  - `odys.optimization.model`
    - `odys.optimization.model.linopy_converter`
    - `odys.optimization.model.milp_model`
    - `odys.optimization.model.model_builder`
    - `odys.optimization.model.objectives`
    - `odys.optimization.model.registry`
    - `odys.optimization.model.sets`
    - `odys.optimization.model.variables`
  - `odys.optimization.parameters`
    - `odys.optimization.parameters.generator_parameters`
    - `odys.optimization.parameters.load_parameters`
    - `odys.optimization.parameters.market_parameters`
    - `odys.optimization.parameters.parameters`
    - `odys.optimization.parameters.scenario_parameters`
    - `odys.optimization.parameters.storage_parameters`
- `odys.results`
  - `odys.results.dispatch`
  - `odys.results.optimization_results`
- `odys.solvers`
  - `odys.solvers.config_translators`
  - `odys.solvers.solver`
  - `odys.solvers.solver_config`
- `odys.utils`
  - `odys.utils.logging`
