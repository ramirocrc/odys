---
icon: lucide/workflow
---

# Sequence diagrams

How the layers of the [data model](data_model.md) interact at run time.

## Pipeline

`EnergySystem.optimize()` is three calls: build the problem, build and solve the model, wrap the outcome.

Participants: [`EnergySystem`](api/energy_system.md), [`OptimizationProblem`](api/optimization/problem.md), [`build_model`](api/optimization/model/model_builder.md), [`solve`](api/solvers/solver.md), [`OptimalDispatchResults`](api/results/optimization_results.md).

```mermaid
sequenceDiagram
    actor User
    participant ES as EnergySystem
    participant OP as OptimizationProblem
    participant MB as build_model
    participant S as solve
    participant R as OptimalDispatchResults
    User->>ES: optimize(solver_config)
    ES->>OP: assemble(entities, horizon, scenario_set, objective)
    OP-->>ES: problem (context, formulations, objective terms)
    ES->>MB: build_model(problem)
    MB-->>ES: linopy.Model
    ES->>S: solve(model, solver_config)
    S-->>ES: SolveOutcome
    ES->>R: OptimalDispatchResults(outcome, problem.dispatches)
    R->>OP: dispatches(solution), only when outcome.has_solution
    OP-->>R: one Dispatch per formulation
    R-->>User: results
```
