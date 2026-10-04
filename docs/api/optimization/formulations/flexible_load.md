---
icon: fontawesome/solid/sliders
---

# `odys.optimization.formulations.flexible_load`

The flexible-load formulation: the load adjustment variable $\Delta d_{l,t,s}$, its bounds, the load's power injection and the value of consumption in the profit.

The adjustment variable is bounded by the maximum decrease and maximum increase:

$$
-\Delta d^{\max-}_l \le \Delta d_{l,t,s} \le \Delta d^{\max+}_l
$$

Its power injection is $-\sum_l (D_{l,t,s} + \Delta d_{l,t,s})$ and its profit per scenario is $\sum_{t,l} \Delta d_{l,t,s}\,\Delta t\,v_l$.

See also [FlexibleLoad](../../domain/entities/flexible_load.md) for the domain model and [entity_arrays](../parameters/entity_arrays.md) for the parameter arrays.

::: odys.optimization.formulations.flexible_load
