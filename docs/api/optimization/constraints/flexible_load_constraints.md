---
icon: fontawesome/solid/sliders
---

# `odys.optimization.constraints.flexible_load_constraints`

Flexible load constraint construction.

The adjustment variable is bounded by the maximum decrease and maximum increase:

$$
-\Delta d^{\max-}_l \le \Delta d_{l,t,s} \le \Delta d^{\max+}_l
$$

See also [FlexibleLoad](../../domain/entities/flexible_load.md) for the domain model and [flexible_load_parameters](../parameters/flexible_load_parameters.md) for the parameter extraction.

::: odys.optimization.constraints.flexible_load_constraints
