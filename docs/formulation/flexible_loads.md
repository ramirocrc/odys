---
icon: lucide/sliders-horizontal
---

# Flexible loads

A cold store can run a bit harder when power is cheap, a process can slow down when it's expensive, a site can cut a few machines for an hour. A flexible load is demand like that: it has a base profile, and the optimizer may move it up or down, within limits, when that pays.

This page covers every `FlexibleLoad`. It's the simplest asset in odys: one decision per step, and a range it has to stay in.

## Sets and indices

Flexible loads live in $\mathcal{L}$, with index $l$. Each one has a base profile $D_{l,s,t}$, from its `LoadProfile` in each scenario: what it would consume if nobody touched it.

## Variables

For each flexible load, scenario and step, odys decides:

- $p^{adj}_{l,s,t}$: the adjustment, in MW. Positive raises the load, negative lowers it.

The load that actually happens is the base plus the adjustment, $D_{l,s,t} + p^{adj}_{l,s,t}$. The results report both: `load_adjustment` and `actual_load`.

## Constraints

Each side of the range can be limited in one of two ways: **relative** to the base (at most so many MW less, or more), or **absolute** (never below, or above, so many MW). You choose one per side, or both.

For example, take a base of 10 MW. With `max_decrease=3` and `max_increase=3`, the actual load can go anywhere from 7 to 13 MW. Add `min_load=8`, and the floor becomes 8 MW, while the top stays at 13 MW.

### FL-1 · Demand moves within its range {#fl-1}

The load never falls below its floor or rises above its ceiling. Each one is either an absolute limit, if you set it, or a step away from the base.

$$
\underline{F}_{l,s,t} \le p^{adj}_{l,s,t} \le \overline{F}_{l,s,t} \qquad \forall l \in \mathcal{L},\ s \in \mathcal{S},\ t \in \mathcal{T}
$$

with the lowest and highest adjustment

$$
\underline{F}_{l,s,t} =
\begin{cases}
\underline{P}_l - D_{l,s,t} & \text{if a minimum load } \underline{P}_l \text{ is set} \\
-\overline{\Delta}^{down}_l & \text{otherwise}
\end{cases}
\qquad
\overline{F}_{l,s,t} =
\begin{cases}
\overline{P}_l - D_{l,s,t} & \text{if a maximum load } \overline{P}_l \text{ is set} \\
\overline{\Delta}^{up}_l & \text{otherwise}
\end{cases}
$$

Read aloud: you can turn the load down or up, but not past the floor or the ceiling.

**Why it looks like this.** Some consumption can always be trimmed or pushed a little, so a limit relative to the base fits. Other loads have a hard minimum to keep running, or can't draw more than their connection allows, so an absolute limit fits. Both are written as a limit on the adjustment, so the model has one variable per load and step, whichever you choose. An absolute limit moves with the base: a high base leaves more room to cut, and less room to grow.

**Good to know.**

- Every flexible load needs a floor and a ceiling: odys asks for `max_decrease` or `min_load`, and for `max_increase` or `max_load`. It also checks that `min_load` isn't above `max_load`.
- When you set both on one side, the absolute limit wins and the relative one is ignored, even when it's the tighter one ([#168](https://github.com/ramirocrc/odys/issues/168)).
- odys checks that the base stays between `min_load` and `max_load`, and, without `min_load`, that `max_decrease` is never above the base. So the actual load can't go negative. It doesn't check that the base itself is non-negative ([#148](https://github.com/ramirocrc/odys/issues/148)).
- The floor and the ceiling are two constraints in the model, one per side.

`Added: always · Binds: when it pays to move the load as far as it goes · Names: flexible_load_adjustment_lower_bound_constraint, flexible_load_adjustment_upper_bound_constraint`

### What a flexible load doesn't do

Every step stands on its own. There's nothing more to a flexible load than FL-1:

- Energy cut now doesn't have to be made up later. A lower load is simply consumption that doesn't happen, not consumption that moves. Shifting load in time is proposed in [#162](https://github.com/ramirocrc/odys/issues/162).
- The adjustment can jump from one end of its range to the other in one step. Ramp limits are proposed in [#79](https://github.com/ramirocrc/odys/issues/79).
- The variable is called `load_adjustment`, without the `flexible_load_` prefix the constraints have ([#161](https://github.com/ramirocrc/odys/issues/161)).

## Power balance contribution

A flexible load takes its actual load from the bus, so it adds

$$
-\left(D_{l,s,t} + p^{adj}_{l,s,t}\right)
$$

to the [power balance](power_balance.md#pb-1) at every step.

Before solving, odys counts the least a flexible load can consume: its `min_load`, or the base minus `max_decrease`. That's what the check on supply has to cover (see [PB-1](power_balance.md#pb-1)).

## Objective contribution

Each flexible load adds the value of its adjustment to the profit $\Pi_s$ of every scenario (see [Objective](objective.md#profit-per-scenario)):

$$
\sum_{l \in \mathcal{L}} \sum_{t \in \mathcal{T}} c^{val}_l\, p^{adj}_{l,s,t}\, \Delta t
$$

Read aloud: every extra MWh you consume is worth $c^{val}_l$, and every MWh you don't is worth that much less.

- This is where the decision comes from: the extra power has to come from somewhere, and its cost sits in the other assets' and markets' terms. How that plays out in a plan is on the [FlexibleLoad](../user_guide/assets/flexible_load.md#value-of-consumption) page.
- Only the adjustment is valued, not the base. The base's value doesn't depend on any decision, so it's left out.

## Where to find each symbol in odys

| Symbol | Attribute | Type | Unit |
| ------ | --------- | ---- | ---- |
| $\mathcal{L}$ | `FlexibleLoad` | Parameter | – |
| $D_{l,s,t}$ | `LoadProfile.values` | Parameter | MW |
| $\underline{P}_l$ | `FlexibleLoad.min_load` | Parameter | MW |
| $\overline{P}_l$ | `FlexibleLoad.max_load` | Parameter | MW |
| $\overline{\Delta}^{down}_l$ | `FlexibleLoad.max_decrease` | Parameter | MW |
| $\overline{\Delta}^{up}_l$ | `FlexibleLoad.max_increase` | Parameter | MW |
| $\underline{F}_{l,s,t}$, $\overline{F}_{l,s,t}$ | the lowest and highest adjustment, from the limits above | Parameter | MW |
| $c^{val}_l$ | `FlexibleLoad.value_of_consumption` | Parameter | currency per MWh |
| $p^{adj}_{l,s,t}$ | `load_adjustment` · `results.flexible_loads.load_adjustment` | Variable · Result | MW |
| $D_{l,s,t} + p^{adj}_{l,s,t}$ | `results.flexible_loads.actual_load` | Result | MW |

You've now seen every piece. Back to the whole model on one screen: see the [Overview](index.md#the-whole-model-on-one-screen).

---

Implemented in [`odys.optimization.formulations.flexible_load`](../developer/api/optimization/formulations/flexible_load.md).
