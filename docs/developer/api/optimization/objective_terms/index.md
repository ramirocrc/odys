---
icon: lucide/target
---

# `odys.optimization.objective_terms`

Model formulations, one per objective term type. An `ObjectiveTermFormulation` adds its own variables and constraints (CVaR's value at risk, shortfalls and shortfall constraint) and returns its weighted expression; the objective is their sum. `OBJECTIVE_TERM_FORMULATIONS` lists every term type's formulation, in build order.

The model maximizes the weighted sum of the objective's terms:

$$
\max\; w_{\text{profit}} \sum_s \pi_s \Pi_s
+ w_{\text{risk}} \left(
\eta - \frac{1}{1-\alpha} \sum_s \pi_s \xi_s
\right)
$$

with the CVaR shortfall constraint:

$$
\xi_s \ge \eta - \Pi_s
$$

The per-scenario profit implementation is:

$$
\Pi_s = \sum_{t,m} \lambda_{m,t,s}\left(v^{sell}_{m,t,s} - v^{buy}_{m,t,s}\right)
- \sum_{t,g}\left(c_g p_{g,t,s} + C^{start}_g y^{start}_{g,t,s}\right)
- \sum_{t,b} C^{deg}_b \, \Delta t \left(p^{ch}_{b,t,s} + p^{dis}_{b,t,s}\right)
$$

See also [domain.objective](../../domain/objective.md) for the public configuration interface.

## Modules

- `base`
- `cvar`
- `profit`

::: odys.optimization.objective_terms
