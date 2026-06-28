---
icon: lucide/target
---

# `odys.domain.objective`

Objective configuration for energy system optimization.

Odys currently builds the objective as a weighted sum of the configured terms:

$$
\max \sum_i w_i\,T_i(model)
$$

In the current configuration, that is the expected profit term plus an optional CVaR term:

$$
\max\; w_{\text{profit}} \sum_s \pi_s \Pi_s
+ w_{\text{risk}} \left(
\eta - \frac{1}{1-\alpha} \sum_s \pi_s \xi_s
\right)
$$

where $\xi_s \ge \eta - \Pi_s$. If no CVaR term is configured, the implementation builds only the expected-profit term.

See also [optimization.model.objectives](../optimization/model/objectives.md) for the implementation-side construction.

::: odys.domain.objective
