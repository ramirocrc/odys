---
icon: fontawesome/solid/plug
---

# `odys.optimization.constraints.charger_constraints`

Charger assignment and power limit constraints.

Each charger can serve at most one EV at a time:

$$
\sum_{v} a_{c,v,t,s} \le 1 \quad \forall c, t, s
$$

Each EV can be connected to at most one charger at a time:

$$
\sum_{c} a_{c,v,t,s} \le 1 \quad \forall v, t, s
$$

where $a_{c,v,t,s} \in \{0, 1\}$ is the binary assignment variable.

Charger power limit (EV charging and discharging power limited by the assigned charger's max power):

$$
p^{ch}_{v,t,s} + p^{dis}_{v,t,s} \le \sum_{c} a_{c,v,t,s} \cdot P^{\max}_c
$$

See also [Charger](../../domain/entities/charger.md) for the domain model and [charger_parameters](../parameters/charger_parameters.md) for the parameter extraction.

::: odys.optimization.constraints.charger_constraints
