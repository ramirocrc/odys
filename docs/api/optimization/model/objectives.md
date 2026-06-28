---
icon: lucide/target
---

# `odys.optimization.model.objectives`

Objective model construction.

The implementation builds the same weighted objective used in the public configuration:

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
$$

See also [domain.objective](../../domain/objective.md) for the public configuration interface.

::: odys.optimization.model.objectives
