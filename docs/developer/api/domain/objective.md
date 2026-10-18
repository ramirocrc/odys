---
icon: lucide/target
---

# `odys.domain.objective`

Objective configuration for energy system optimization.

An `Objective` holds its terms: a required `ProfitTerm` and an optional `CVaRTerm`, at most one of each. The model maximizes the sum of their weighted expressions; without a `CVaRTerm`, that is the expected profit alone. The terms are written out on the [Objective](../../../formulation/objective.md#combined-objective) formulation page, and configuring them on the [Risk (CVaR)](../../../user_guide/uncertainty/risk.md) User Guide page.

See also [optimization.objective_terms](../optimization/objective_terms/index.md) for the implementation-side construction.

::: odys.domain.objective
