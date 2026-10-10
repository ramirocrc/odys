---
icon: fontawesome/solid/chart-line
---

# `odys.optimization.formulations.energy_market`

The energy market formulation: sell and buy volumes and the trade mode, their constraints, the markets' power injection $\sum_m (v^{buy}_{m,t,s} - v^{sell}_{m,t,s})$ and the trading revenue in the profit.

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

For `stage_fixed` markets (non-anticipativity), each market variable is pinned to its first-scenario value:

$$
x_{m,t,s} - x_{m,t,s_0} = 0 \quad \forall s
$$

This applies to the sell volume, buy volume and trade mode.

See also [Market](../../domain/entities/market.md) for the domain model and [entity_arrays](../../parameters/entity_arrays.md) for the parameter arrays.

::: odys.optimization.formulations.energy_market
