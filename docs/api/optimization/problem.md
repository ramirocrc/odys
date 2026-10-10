---
icon: lucide/package
---

# `odys.optimization.problem`

Internal implementation detail. `OptimizationProblem` is the input of the model builder: the context, one formulation per entity type present and one per objective term. `OptimizationProblem.assemble()` builds the formulations, and `EnergySystem.build_problem()` calls it.

::: odys.optimization.problem
