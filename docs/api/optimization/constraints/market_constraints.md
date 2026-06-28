---
icon: fontawesome/solid/chart-line
---

# `odys.optimization.constraints.market_constraints`

Market constraint construction.

Trading volumes are bounded by the market limit:

$$
0 \le v^{sell}_{m,t,s} \le V^{\max}_m, \qquad 0 \le v^{buy}_{m,t,s} \le V^{\max}_m, \qquad z_{m,t,s} \in \{0,1\}
$$

Buy and sell are mutually exclusive through the binary trade-mode variable:

$$
v^{sell}_{m,t,s} \le z_{m,t,s} V^{\max}_m
$$

$$
v^{buy}_{m,t,s} + z_{m,t,s} V^{\max}_m \le V^{\max}_m
$$

Trade-direction constraints fix the unavailable direction to zero for buy-only or sell-only markets.

See also [Market](../../domain/entities/market.md) for the domain model and [market_parameters](../parameters/market_parameters.md) for the parameter extraction.

::: odys.optimization.constraints.market_constraints
