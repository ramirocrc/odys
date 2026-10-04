---
icon: fontawesome/solid/car
---

# `odys.optimization.formulations.electric_vehicle`

The electric vehicle formulation: the shared battery model (see [storage](storage.md)) with trip energy drawn while driving, plus the driving and departure-SOC constraints. Vehicles charge and discharge only through chargers (see [charging](charging.md)).

EVs inherit storage physics and add trip-driven constraints. The SOC dynamics include trip energy consumption:

$$
SOC_{v,t,s} = SOC_{v,t-1,s}
+ \eta^{ch}_v \frac{\Delta t}{E_v} p^{ch}_{v,t,s}
- \frac{\Delta t}{\eta^{dis}_v E_v} p^{dis}_{v,t,s}
- \frac{e^{trip}_{v,t}}{E_v}
$$

where $e^{trip}_{v,t}$ is the trip energy consumed at timestep $t$. The first step starts from the initial SOC and draws a trip departing at $t=0$ the same way:

$$
SOC_{v,0,s} = SOC^{start}_v
+ \eta^{ch}_v \frac{\Delta t}{E_v} p^{ch}_{v,0,s}
- \frac{\Delta t}{\eta^{dis}_v E_v} p^{dis}_{v,0,s}
- \frac{e^{trip}_{v,0}}{E_v}
$$

Driving constraint (no charging or discharging while driving):

$$
p^{ch}_{v,t,s} + p^{dis}_{v,t,s} \le (P^{\max,ch}_v + P^{\max,dis}_v)(1 - d_{v,t})
$$

where $d_{v,t} \in \{0, 1\}$ indicates whether the vehicle is driving.

Minimum SoC at departure:

$$
SOC_{v,t-1,s} \ge SOC^{min,dep}_{v,t}
$$

See also [ElectricVehicle](../../domain/entities/electric_vehicle.md) for the domain model and [entity_arrays](../parameters/entity_arrays.md) for the parameter arrays.

::: odys.optimization.formulations.electric_vehicle
