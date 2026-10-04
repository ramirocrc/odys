---
icon: lucide/package
---

# `odys.optimization.problem`

Internal implementation detail. `OptimizationProblem` is the input of the model builder: one formulation per entity type present, plus the context and the objective. `per_scenario_profit()` sums the formulations' profits. `EnergySystem.build_problem()` builds it.

::: odys.optimization.problem
