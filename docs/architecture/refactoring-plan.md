# Odys Hexagonal Architecture Refactoring Plan

## Overview

Complete restructure of Odys into a hexagonal architecture with clear boundaries between domain, application, adapters, and infrastructure layers.

## Target Directory Structure

```
src/odys/
├── __init__.py                    # Public API exports
├── domain/                        # Pure business logic (no external deps)
│   ├── __init__.py
│   ├── exceptions.py             # OdysError hierarchy
│   ├── entities/                 # Core domain entities
│   │   ├── __init__.py
│   │   ├── base.py               # EnergyAsset abstract base
│   │   ├── generator.py
│   │   ├── storage.py
│   │   ├── load.py
│   │   ├── energy_market.py
│   │   └── scenario.py
│   ├── value_objects/            # Immutable value types
│   │   ├── __init__.py
│   │   ├── power.py             # Power with unit conversion
│   │   ├── energy.py            # Energy quantities
│   │   ├── cost.py              # Cost value
│   │   └── time_step.py         # Timestep duration
│   ├── ports/                    # Abstract interfaces (hexagon ports)
│   │   ├── __init__.py
│   │   ├── model_builder.py     # IModelBuilder protocol
│   │   ├── solver.py            # ISolver protocol
│   │   ├── validator.py        # IValidator protocol
│   │   └── results_reader.py    # IResultsReader protocol
│   ├── objective.py              # Objective function config
│   └── services/                 # Domain services
│       ├── __init__.py
│       ├── energy_balance.py    # Energy balance calculations
│       └── feasibility.py       # Feasibility checks
│
├── application/                  # Use cases (orchestration)
│   ├── __init__.py
│   ├── optimize_energy_system.py # Main use case
│   ├── dto.py                    # Data transfer objects
│   └── ports.py                  # Application-level ports
│
├── adapters/                      # Concrete implementations
│   ├── __init__.py
│   ├── primary/                  # Driving adapters (input)
│   │   ├── __init__.py
│   │   ├── asset_adapter.py     # Converts user input to domain entities
│   │   ├── scenario_adapter.py  # Scenario normalization
│   │   └── market_adapter.py    # Market validation
│   │
│   ├── secondary/               # Driven adapters (output)
│   │   ├── __init__.py
│   │   ├── model/
│   │   │   ├── __init__.py
│   │   │   ├── milp_model.py   # EnergyMILPModel wrapper
│   │   │   ├── builder.py      # MathModelAdapter (IModelBuilder)
│   │   │   └── constraints/
│   │   │       ├── __init__.py
│   │   │       ├── base.py
│   │   │       ├── generator.py
│   │   │       ├── storage.py
│   │   │       ├── market.py
│   │   │       ├── scenario.py
│   │   │       └── cvar.py
│   │   ├── solver/
│   │   │   ├── __init__.py
│   │   │   ├── base.py         # Base solver adapter
│   │   │   ├── highs.py        # HiGHSSolverAdapter
│   │   │   ├── gurobi.py       # GurobiSolverAdapter
│   │   │   └── cplex.py        # CPLEXSolverAdapter
│   │   ├── results/
│   │   │   ├── __init__.py
│   │   │   └── linopy_adapter.py # IResultsReader impl
│   │   └── validation/
│   │       ├── __init__.py
│   │       └── pydantic_validator.py
│
└── infrastructure/               # Framework wiring
    ├── __init__.py
    ├── di_container.py          # Dependency injection
    └── results.py               # Result containers
```

## Port Interfaces (Domain Contracts)

### IModelBuilder
```python
class IModelBuilder(Protocol):
    def build(self, parameters: DomainParameters) -> OptimizationModel: ...
    def add_variable(self, name: str, dims: list[str], **kwargs) -> Variable: ...
    def add_constraint(self, name: str, constraint: Constraint) -> None: ...
    def set_objective(self, expression: Expression, sense: str) -> None: ...
```

### ISolver
```python
class ISolver(Protocol):
    def solve(self, model: OptimizationModel, config: SolverConfig) -> SolverResult: ...
    def supports(self, solver_name: str) -> bool: ...
```

### IValidator
```python
class IValidator(Protocol):
    def validate(self, entity: Any) -> ValidationResult: ...
    def validate_system(self, system: EnergySystem) -> ValidationResult: ...
```

## Migration Phases

### Phase 1: Create Domain Core
1. Create `src/odys/domain/` structure
2. Move entities (Generator, Storage, Load, EnergyMarket, Scenario)
3. Create value objects (Power, Energy, Cost)
4. Define port interfaces (IModelBuilder, ISolver, IValidator)
5. Move exceptions to domain

### Phase 2: Create Application Layer
1. Create `src/odys/application/` structure
2. Implement `OptimizeEnergySystemUseCase`
3. Create DTOs for input/output
4. Define application ports

### Phase 3: Create Adapters
1. Create `src/odys/adapters/` structure
2. Implement primary adapters (input)
3. Move and refactor math model to `MathModelAdapter`
4. Implement solver adapters
5. Implement validation adapter

### Phase 4: Create Infrastructure
1. Create `src/odys/infrastructure/` structure
2. Implement DI container
3. Wire up adapters

### Phase 5: Update Public API
1. Update `__init__.py` exports
2. Deprecate old imports (optional migration helpers)
3. Update examples and docs

## Breaking Changes

| Old Import | New Import |
|------------|------------|
| `odys.EnergySystem` | `odys.application.OptimizeEnergySystemUseCase` |
| `odys.Generator` | `odys.domain.entities.Generator` |
| `odys.energy_system_models` | `odys.domain.entities` |

## Benefits

1. **Testability**: Domain logic tested without external dependencies
2. **Swappability**: Easy to swap solvers, validators, model builders
3. **Clarity**: Clear separation of concerns
4. **Extensibility**: Add new adapters without touching domain
5. **Maintainability**: Changes localized to appropriate layer
