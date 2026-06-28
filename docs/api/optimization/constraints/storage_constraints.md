---
icon: fontawesome/solid/battery-three-quarters
---

# `odys.optimization.constraints.storage_constraints`

Storage constraint construction.

Charge and discharge power are bounded by the binary charging mode:

$$
0 \le p^{ch}_{b,t,s}, \qquad 0 \le p^{dis}_{b,t,s}, \qquad 0 \le SOC_{b,t,s}, \qquad z_{b,t,s} \in \{0,1\}
$$

$$
p^{ch}_{b,t,s} \le z_{b,t,s} P^{\max}_b
$$

$$
p^{dis}_{b,t,s} + z_{b,t,s} P^{\max}_b \le P^{\max}_b
$$

The core SOC dynamics are:

$$
SOC_{b,t,s} = SOC_{b,t-1,s}
+ \eta^{ch}_b \frac{\Delta t}{E_b} p^{ch}_{b,t,s}
- \frac{\Delta t}{\eta^{dis}_b E_b} p^{dis}_{b,t,s}
$$

for $t > 0$. At the first timestep:

$$
SOC_{b,0,s} = SOC^{start}_b
+ \eta^{ch}_b \frac{\Delta t}{E_b} p^{ch}_{b,0,s}
- \frac{\Delta t}{\eta^{dis}_b E_b} p^{dis}_{b,0,s}
$$

The implementation also applies SOC bounds, the final SOC constraint, and the net-power definition:

$$
SOC^{min}_b \le SOC_{b,t,s} \le SOC^{max}_b, \qquad SOC_{b,t,s} \le 1
$$

$$
SOC_{b,T,s} = SOC^{end}_b
$$

$$
p^{net}_{b,t,s} = p^{ch}_{b,t,s} - p^{dis}_{b,t,s}
$$

See also [Storage](../../domain/entities/storage.md) for the domain model and [storage_parameters](../parameters/storage_parameters.md) for the parameter extraction.

::: odys.optimization.constraints.storage_constraints
