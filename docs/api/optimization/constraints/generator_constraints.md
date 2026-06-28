---
icon: fontawesome/solid/bolt
---

# `odys.optimization.constraints.generator_constraints`

Generator constraint construction.

This module encodes the main generator limits used by the MILP model:

$$
0 \le p_{g,t,s}, \qquad u_{g,t,s}, y^{start}_{g,t,s}, y^{shutdown}_{g,t,s} \in \{0,1\}
$$

$$
p_{g,t,s} - P^{\max}_g u_{g,t,s} \le 0
$$

$$
p_{g,t,s} \ge \epsilon_g u_{g,t,s}
$$

$$
p_{g,t,s} \ge P^{\min}_g u_{g,t,s}
$$

$$
p_{g,t,s} - p_{g,t-1,s} \le R^{up}_g, \qquad p_{g,t-1,s} - p_{g,t,s} \le R^{down}_g
$$

Startup and shutdown indicators are constrained as:

$$
y^{start}_{g,t,s} \ge u_{g,t,s} - u_{g,t-1,s}, \qquad y^{start}_{g,t,s} \le u_{g,t,s}
$$

$$
y^{start}_{g,t,s} + u_{g,t-1,s} \le 1
$$

$$
y^{shutdown}_{g,t,s} \ge u_{g,t-1,s} - u_{g,t,s}, \qquad y^{shutdown}_{g,t,s} \le u_{g,t-1,s}
$$

$$
y^{shutdown}_{g,t,s} + u_{g,t,s} \le 1
$$

Minimum up time is enforced as:

$$
\sum_{\tau=t-U_g+1}^{t} u_{g,\tau,s} \ge U_g y^{shutdown}_{g,t+1,s}
$$

See also [Generator](../../domain/entities/generator.md) for the domain model and [generator_parameters](../parameters/generator_parameters.md) for the parameter extraction.

::: odys.optimization.constraints.generator_constraints
