---
icon: lucide/file-text
---

# `odys.optimization.constraints.scenario_constraints`

Scenario-level constraint construction.

The power balance is assembled as one left-hand side and constrained to zero:

$$
\sum_g p_{g,t,s}
+ \sum_b p^{dis}_{b,t,s}
- \sum_b p^{ch}_{b,t,s}
+ \sum_m v^{buy}_{m,t,s}
- \sum_m v^{sell}_{m,t,s}
- \sum_l d_{l,t,s}
= 0
$$

If available-capacity profiles are provided, generator power is capped by them:

$$
p_{g,t,s} \le A_{g,t,s}
$$

For `stage_fixed` markets, each market variable is pinned to its first-scenario value:

$$
x_{m,t,s} - x_{m,t,s_0} = 0 \quad \forall s
$$

This applies to market buy volume, sell volume, and trade mode.

See also [Scenarios](../../domain/scenarios.md) for the domain model and [scenario_parameters](../parameters/scenario_parameters.md) for the parameter extraction.

::: odys.optimization.constraints.scenario_constraints
