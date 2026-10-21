---
icon: lucide/sliders-horizontal
---

# Flexible loads

A cold store can run a bit harder when power is cheap, a process can slow down when it's expensive, a site can cut a few machines for an hour. A flexible load is demand like that: at every step it has a range it can run in, and the optimizer picks where in that range it runs, when that pays.

This page covers every `FlexibleLoad`. It's the simplest asset in odys: one decision per step, and a range it has to stay in.

## Sets and indices

Flexible loads live in $\mathcal{L}$, with index $l$. Each one has a range from its `FlexibleLoadProfile` in each scenario: a lower bound $\underline{D}_{l,s,t}$, the least it consumes, and an upper bound $\overline{D}_{l,s,t}$, the most.

## Variables

For each flexible load, scenario and step, odys decides:

- $d_{l,s,t} \ge 0$: the consumption, in MW. The results report it as `consumption`.

## Constraints

### FL-1 · Demand stays within its range {#fl-1}

The load never consumes less than its lower bound or more than its upper bound.

$$
\underline{D}_{l,s,t} \le d_{l,s,t} \le \overline{D}_{l,s,t} \qquad \forall l \in \mathcal{L},\ s \in \mathcal{S},\ t \in \mathcal{T}
$$

Read aloud: you can run the load anywhere from its floor to its ceiling.

**Why it looks like this.** Without a floor, the optimizer would switch the load off whenever power costs more than the load is worth. Without a ceiling, it would run the load without limit whenever power is cheap. Each bound is given per step and per scenario, because what a process can do changes over the day (a shift pattern, a minimum to keep a furnace warm) and between futures (an order book that may or may not fill).

**Good to know.**

- odys checks that both bounds are at least 0 and that the lower bound isn't above the upper one, at every step. When the load has `min_load` or `max_load`, its bounds must also stay within them. So the consumption can never be negative.
- The floor and the ceiling are two constraints in the model, one per side.

`Added: always · Binds: when it pays to run the load as low or as high as it goes · Names: flexible_load_lower_bound_constraint, flexible_load_upper_bound_constraint`

### What a flexible load doesn't do

Every step stands on its own. There's nothing more to a flexible load than FL-1:

- Energy not used now doesn't have to be used later. Lower consumption is simply consumption that doesn't happen, not consumption that moves. Shifting load in time is proposed in [#162](https://github.com/ramirocrc/odys/issues/162).
- The consumption can jump from one end of its range to the other in one step. Ramp limits are proposed in [#79](https://github.com/ramirocrc/odys/issues/79).

## Power balance contribution

A flexible load takes its consumption from the bus, so it adds

$$
-d_{l,s,t}
$$

to the [power balance](power_balance.md#pb-1) at every step.

Before solving, odys counts the least a flexible load can consume, its lower bound. That's what the check on supply has to cover (see [PB-1](power_balance.md#pb-1)).

## Objective contribution

Each flexible load adds the value of its consumption to the profit $\Pi_s$ of every scenario (see [Objective](objective.md#profit-per-scenario)):

$$
\sum_{l \in \mathcal{L}} \sum_{t \in \mathcal{T}} c^{val}_l\, d_{l,s,t}\, \Delta t
$$

Read aloud: every MWh you consume is worth $c^{val}_l$.

- This is where the decision comes from: the power has to come from somewhere, and its cost sits in the other assets' and markets' terms. How that plays out in a plan is on the [FlexibleLoad](../user_guide/assets/flexible_load.md#value-of-consumption) page.
- All of the consumption is valued, including the part the lower bound forces. That part doesn't change the plan, but it is in the objective value, and in each scenario's profit that the [risk term](objective.md#conditional-value-at-risk) weighs.

## Where to find each symbol in odys

| Symbol | Attribute | Type | Unit |
| ------ | --------- | ---- | ---- |
| $\mathcal{L}$ | `FlexibleLoad` | Parameter | – |
| $\underline{D}_{l,s,t}$ | `FlexibleLoadProfile.lower_bound` | Parameter | MW |
| $\overline{D}_{l,s,t}$ | `FlexibleLoadProfile.upper_bound` | Parameter | MW |
| $c^{val}_l$ | `FlexibleLoad.value_of_consumption` | Parameter | currency per MWh |
| $d_{l,s,t}$ | `flexible_load_consumption` · `results.flexible_loads.consumption` | Variable · Result | MW |

You've now seen every piece. Back to the whole model on one screen: see the [Overview](index.md#the-whole-model-on-one-screen).

---

Implemented in [`odys.optimization.formulations.flexible_load`](../developer/api/optimization/formulations/flexible_load.md).
