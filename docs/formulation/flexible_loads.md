---
icon: lucide/sliders-horizontal
---

# Flexible loads

A cold store can run a bit harder when power is cheap, a process can slow down when it's expensive, a site can cut a few machines for an hour. A flexible load is demand like that: at every step it has a range it can run in, and the optimizer picks where in that range it runs, when that pays.

This page covers every `FlexibleLoad`. At its simplest it's one decision per step and a range to stay in. An industrial process can add two things a generator has too: it changes only so fast, and it can be switched off.

## Sets and indices

Flexible loads live in $\mathcal{L}$, with index $l$. Each one has a range from its `FlexibleLoadProfile` in each scenario: a lower bound $\underline{D}_{l,s,t}$, the least it consumes while it runs, and an upper bound $\overline{D}_{l,s,t}$, the most. The loads with a `commitment`, which can be switched off, form $\mathcal{L}^{sw} \subseteq \mathcal{L}$.

## Variables

For each flexible load, scenario and step, odys decides:

- $d_{l,s,t} \ge 0$: the consumption, in MW. The results report it as `consumption`.

When at least one flexible load has a commitment, every flexible load also gets the three binaries a generator has:

- $u_{l,s,t} \in \{0, 1\}$: 1 while the load runs (`status`);
- $y^{start}_{l,s,t}, y^{stop}_{l,s,t} \in \{0, 1\}$: 1 at the step it starts or stops (`startup`, `shutdown`).

Without any commitment, there are no binaries, and the results report every load as on, with no starts or stops. Below, $u_{l,s,t} = 1$ and $y^{start}_{l,s,t} = y^{stop}_{l,s,t} = 0$ in that case.

## Constraints

### FL-1 · Demand stays within its range while it runs {#fl-1}

While it runs, the load never consumes less than its lower bound or more than its upper bound. While it's off, it consumes nothing.

$$
\underline{D}_{l,s,t}\, u_{l,s,t} \le d_{l,s,t} \le \overline{D}_{l,s,t}\, u_{l,s,t} \qquad \forall l \in \mathcal{L},\ s \in \mathcal{S},\ t \in \mathcal{T}
$$

Read aloud: you can run the load anywhere from its floor to its ceiling, or, if it can switch off, not at all.

**Why it looks like this.** Without a floor, the optimizer would turn the load down to nothing whenever power costs more than the load is worth. Without a ceiling, it would run the load without limit whenever power is cheap. Each bound is given per step and per scenario, because what a process can do changes over the day (a shift pattern, a minimum to keep a furnace warm) and between futures (an order book that may or may not fill).

**Good to know.**

- odys checks that both bounds are at least 0 and that the lower bound isn't above the upper one, at every step. When the load has `min_load` or `max_load`, its bounds must also stay within them. So the consumption can never be negative.
- The floor and the ceiling are two constraints in the model, one per side.
- For a load that can switch off, the lower bound is its minimum stable load: it runs at least that much, or not at all.

`Added: always · Binds: when it pays to run the load as low or as high as it goes · Names: flexible_load_lower_bound_constraint, flexible_load_upper_bound_constraint`

### FL-2 · A load switches on and off like a generator {#fl-2}

A load with a commitment starts, stops and stays in each state the way a generator does. A load without one stays on.

$$
u_{l,s,t} = 1 \qquad \forall l \in \mathcal{L} \setminus \mathcal{L}^{sw},\ s \in \mathcal{S},\ t \in \mathcal{T}
$$

and, for every flexible load, the generator rows with $l$ in place of $g$:

- start-ups and shut-downs are counted from the status, as in [G-5](generators.md#g-5) and [G-6](generators.md#g-6), from the initial status at $t = 0$;
- once started, the load runs for at least `min_up_time`, and once stopped, it stays off for at least `min_down_time`, counting the time before the run, as in [G-8](generators.md#g-8) and [G-9](generators.md#g-9).

Read aloud: a kiln that can stop pays to start again, and once it's running it keeps running for a while.

**Why it looks like this.** A process with a minimum stable load can't just turn down a little more: it has to stop. Stopping and starting cost money, wear and time, which is what a generator's `Commitment` already describes, so a flexible load takes the same one, and the same rows. A load without a commitment gets the always-on row only when another flexible load has the binaries; otherwise it has none.

**Good to know.**

- The binaries exist only when some flexible load has a commitment, so a model of loads without one stays linear.
- At $t = 0$ the status before the run comes from the load's `FlexibleLoadInitialState`: running if its `power` is above 0, or always for a load without a commitment. Without an initial state, a load with a commitment starts off.
- Every flexible load gets the rows, even one that can't switch off, for which they decide nothing.

`Added: when some flexible load has a commitment (the time-zero rows only when a load starts within its minimum time) · Binds: with min_up_time, min_down_time or start-up and shut-down costs · Names: flexible_load_always_on_constraint, flexible_load_startup_lower_bound_constraint, flexible_load_startup_upper_bound_1_constraint, flexible_load_startup_upper_bound_2_constraint, flexible_load_shutdown_lower_bound_constraint, flexible_load_shutdown_upper_bound_1_constraint, flexible_load_shutdown_upper_bound_2_constraint, flexible_load_min_uptime_{name}_constraint, flexible_load_min_downtime_{name}_constraint, flexible_load_initial_min_uptime_constraint, flexible_load_initial_min_downtime_constraint`

### FL-3 · Consumption rises gradually {#fl-3}

Between two steps the load runs, the consumption rises at most by the ramp-up rate times the step length. A start can land anywhere in the range.

$$
d_{l,s,t} - d_{l,s,t-1} \le \overline{R}^{up}_l\, \Delta t + \overline{D}_{l,s,t}\, y^{start}_{l,s,t} \qquad \forall l \in \mathcal{L} \text{ with } \overline{R}^{up}_l,\ s \in \mathcal{S},\ t \in \mathcal{T}
$$

with $d_{l,s,-1} = P^{init}_l$, the `power` of its initial state.

Read aloud: a running kiln heats up only so fast, but it can start straight at any load it can run at.

**Why it looks like this.** A process changes its draw at a rate set by its physics, in MW per hour, so the step allows that rate times its length. A start is different: a kiln goes from off to its minimum stable load at once, which a ramp from 0 would forbid whenever the minimum is above one step's ramp. The start-up term lifts the limit by the most the load can consume, so it never binds at a start.

**Good to know.**

- The row exists only for the loads with `ramp_up` set.
- At $t = 0$ it counts from the initial power, which is why odys asks for a `FlexibleLoadInitialState` when a ramp is set.

`Added: when some flexible load has ramp_up · Binds: when the load would rise faster than it can · Name: flexible_load_max_ramp_up_constraint`

### FL-4 · Consumption falls gradually {#fl-4}

Between two steps the load runs, the consumption falls at most by the ramp-down rate times the step length. A stop drops straight to 0.

$$
d_{l,s,t-1} - d_{l,s,t} \le \overline{R}^{down}_l\, \Delta t + \overline{D}_{l,s,t-1}\, y^{stop}_{l,s,t} \qquad \forall l \in \mathcal{L} \text{ with } \overline{R}^{down}_l,\ s \in \mathcal{S},\ t \in \mathcal{T}
$$

with $d_{l,s,-1} = P^{init}_l$ and $\overline{D}_{l,s,-1} = P^{init}_l$.

Read aloud: a running kiln cools down only so fast, but it can be switched off at once.

**Why it looks like this.** It mirrors FL-3: the same rate per hour, and a shut-down term large enough, the most the load consumed the step before, that a stop never binds.

`Added: when some flexible load has ramp_down · Binds: when the load would fall faster than it can · Name: flexible_load_max_ramp_down_constraint`

### What a flexible load doesn't do

- Energy not used now doesn't have to be used later. Lower consumption is simply consumption that doesn't happen, not consumption that moves. Shifting load in time is proposed in [#162](https://github.com/ramirocrc/odys/issues/162).
- Ramps don't apply at a start or a stop, unlike a generator's ([G-7](generators.md#g-7)).

## Power balance contribution

A flexible load takes its consumption from the bus, so it adds

$$
-d_{l,s,t}
$$

to the [power balance](power_balance.md#pb-1) at every step.

Before solving, odys counts the least a flexible load can consume: its lower bound, or 0 for a load that can switch off. That's what the check on supply has to cover (see [PB-1](power_balance.md#pb-1)).

## Objective contribution

Each flexible load adds the value of its consumption, less what its starts and stops cost, to the profit $\Pi_s$ of every scenario (see [Objective](objective.md#profit-per-scenario)):

$$
\sum_{l \in \mathcal{L}} \sum_{t \in \mathcal{T}} \left(c^{val}_l\, d_{l,s,t}\, \Delta t - c^{start}_l\, y^{start}_{l,s,t} - c^{stop}_l\, y^{stop}_{l,s,t}\right)
$$

Read aloud: every MWh you consume is worth $c^{val}_l$, and every start and stop costs what its commitment says.

- This is where the decision comes from: the power has to come from somewhere, and its cost sits in the other assets' and markets' terms. How that plays out in a plan is on the [FlexibleLoad](../user_guide/assets/flexible_load.md#value-of-consumption) page.
- All of the consumption is valued, including the part the lower bound forces. That part doesn't change the plan, but it is in the objective value, and in each scenario's profit that the [risk term](objective.md#conditional-value-at-risk) weighs.

## Where to find each symbol in odys

| Symbol | Attribute | Type | Unit |
| ------ | --------- | ---- | ---- |
| $\mathcal{L}$ | `FlexibleLoad` | Parameter | – |
| $\underline{D}_{l,s,t}$ | `FlexibleLoadProfile.lower_bound` | Parameter | MW |
| $\overline{D}_{l,s,t}$ | `FlexibleLoadProfile.upper_bound` | Parameter | MW |
| $\mathcal{L}^{sw}$ | flexible loads with a `FlexibleLoad.commitment` | Parameter | – |
| $c^{val}_l$ | `FlexibleLoad.value_of_consumption` | Parameter | currency per MWh |
| $\overline{R}^{up}_l$, $\overline{R}^{down}_l$ | `FlexibleLoad.ramp_up`, `FlexibleLoad.ramp_down` | Parameter | MW per hour |
| $c^{start}_l$, $c^{stop}_l$ | `FlexibleLoad.commitment.startup_cost`, `FlexibleLoad.commitment.shutdown_cost` | Parameter | currency per event |
| $P^{init}_l$ | `FlexibleLoadInitialState.power` | Parameter | MW |
| $d_{l,s,t}$ | `flexible_load_consumption` · `results.flexible_loads.consumption` | Variable · Result | MW |
| $u_{l,s,t}$ | `flexible_load_status` · `results.flexible_loads.status` | Variable · Result | – |
| $y^{start}_{l,s,t}$, $y^{stop}_{l,s,t}$ | `flexible_load_startup`, `flexible_load_shutdown` · `results.flexible_loads.startup`, `.shutdown` | Variable · Result | – |

You've now seen every piece. Back to the whole model on one screen: see the [Overview](index.md#the-whole-model-on-one-screen).

---

Implemented in [`odys.optimization.formulations.flexible_load`](../developer/api/optimization/formulations/flexible_load.md).
