---
icon: lucide/package
---

# `odys.optimization.problem`

Internal implementation detail. `OptimizationProblem` is the optimization model of one energy system: the context, one formulation per entity type present, one per objective term, and the linopy model they were built into. `OptimizationProblem.assemble()` builds the formulations and the model, and `EnergySystem.build_problem()` calls it.

::: odys.optimization.problem
