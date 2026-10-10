---
icon: lucide/scale
---

# `odys.optimization.power_balance`

The power balance: at every scenario and timestep, the net power injected into the bus is zero.

$$
\sum_g p_{g,t,s}
+ \sum_b p^{dis}_{b,t,s}
- \sum_b p^{ch}_{b,t,s}
+ \sum_m v^{buy}_{m,t,s}
- \sum_m v^{sell}_{m,t,s}
- \sum_l d_{l,t,s}
- \sum_l (D_{l,t,s} + \Delta d_{l,t,s})
= 0
$$

Every entity type contributes its `Formulation.power_injection()`; charging returns none, since the EV formulation already counts the charging power.

::: odys.optimization.power_balance
