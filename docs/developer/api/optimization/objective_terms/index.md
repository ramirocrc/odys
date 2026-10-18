---
icon: lucide/target
---

# `odys.optimization.objective_terms`

Model formulations, one per objective term type. An `ObjectiveTermFormulation` adds its own variables and constraints (CVaR's value at risk, shortfalls and shortfall constraint) and returns its weighted expression; the objective is their sum. `OBJECTIVE_TERM_FORMULATIONS` lists every term type's formulation, in build order.

The model maximizes the sum of the terms' weighted expressions. The expected profit, the CVaR term with its shortfall constraint [CV-1](../../../../formulation/objective.md#cv-1), and their sum are written out on the [Objective](../../../../formulation/objective.md) formulation page.

See also [domain.objective](../../domain/objective.md) for the public configuration interface.

## Modules

- `base`
- `cvar`
- `profit`

::: odys.optimization.objective_terms
