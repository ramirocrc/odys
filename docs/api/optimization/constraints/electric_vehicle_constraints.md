---
icon: fontawesome/solid/car
---

# `odys.optimization.constraints.electric_vehicle_constraints`

Electric vehicle constraint construction.

EVs inherit storage physics and add trip-driven constraints. The SOC dynamics include trip energy consumption:

$$
SOC_{v,t,s} = SOC_{v,t-1,s}
+ \eta^{ch}_v \frac{\Delta t}{E_v} p^{ch}_{v,t,s}
- \frac{\Delta t}{\eta^{dis}_v E_v} p^{dis}_{v,t,s}
- \frac{e^{trip}_{v,t}}{E_v}
$$

where $e^{trip}_{v,t}$ is the trip energy consumed at timestep $t$.

Driving constraint (no charging or discharging while driving):

$$
p^{ch}_{v,t,s} + p^{dis}_{v,t,s} \le (P^{\max,ch}_v + P^{\max,dis}_v)(1 - d_{v,t})
$$

where $d_{v,t} \in \{0, 1\}$ indicates whether the vehicle is driving.

Minimum SoC at departure:

$$
SOC_{v,t-1,s} \ge SOC^{min,dep}_{v,t}
$$

See also [ElectricVehicle](../../domain/entities/electric_vehicle.md) for the domain model and [electric_vehicle_parameters](../parameters/electric_vehicle_parameters.md) for the parameter extraction.

::: odys.optimization.constraints.electric_vehicle_constraints
