---
icon: lucide/book-open
---

# Notation and conventions

Every page in this section speaks the same small language. Skim this page now so the symbols look familiar, and come back whenever one of them doesn't. Each symbol means exactly one thing, on every page.

## Sets and indices

Everything odys models lives in a few sets. A lowercase letter picks one element:

| Set | What it holds | Index | In odys |
| --- | ------------- | ----- | ------- |
| $\mathcal{T} = \{0, \dots, T-1\}$ | The timesteps of the run | $t$ | `number_of_steps` $= T$ |
| $\mathcal{S}$ | The scenarios | $s$ | the `Scenario`s of the `EnergySystem` |
| $\mathcal{G}$ | Generators | $g$ | `Generator` |
| $\mathcal{B}$ | Stationary storages | $b$ | `StationaryStorage` |
| $\mathcal{E}$ | Electric vehicles | $e$ | `ElectricVehicle` |
| $\mathcal{K} = \mathcal{B} \cup \mathcal{E}$ | Every battery, at a fixed site or on wheels | $k$ | `Battery` |
| $\mathcal{C}$ | Chargers | $c$ | `Charger` |
| $\mathcal{L}$ | Flexible loads | $l$ | `FlexibleLoad` |
| $\mathcal{L}^{fix}$ | Fixed loads | $l$ | `FixedLoad` |
| $\mathcal{M}$ | Markets | $m$ | `EnergyMarket` |
| $\mathcal{M}^{fix} \subseteq \mathcal{M}$ | Stage-fixed markets | $m$ | `EnergyMarket(stage_fixed=True)` |

Time starts at 0, like in the code: the first step is $t = 0$ and the last one is $t = T - 1$.

Indices always come in the same order: **asset, scenario, time**. So $p_{g,s,t}$ reads "the power of generator $g$ in scenario $s$ at step $t$". A symbol without $s$ is the same in every scenario, and a symbol without $t$ is the same at every step.

One more letter: $\tau$ only ever appears as the counter inside a sum over a window of steps (the minimum up and down times on the [Generators](generators.md) page).

## Symbol convention

You can tell what a symbol is from how it looks:

| Kind | Style | Examples |
| ---- | ----- | -------- |
| Decisions the optimizer makes | lowercase Latin | power $p$, state of charge $\mathrm{soc}$, on/off status $u$ |
| Things you give odys: sizes and profiles | uppercase Latin | battery capacity $E_k$, demand $D_{l,s,t}$, available capacity $A_{g,s,t}$ |
| Upper and lower limits | a bar over or under the letter | rated power $\overline{P}_g$, minimum power $\underline{P}_g$, minimum state of charge $\underline{\mathrm{soc}}_k$ |
| Costs and values | lowercase $c$ | variable cost $c^{var}_g$, start-up cost $c^{start}_g$, degradation cost $c^{deg}_k$ |
| Rates, efficiencies, prices, probabilities | Greek | charging efficiency $\eta^{ch}_k$, self-discharge $\delta_k$, price $\lambda_{m,s,t}$, probability $\pi_s$ |

The only decisions written in Greek are the two helper variables of the risk term, $\zeta$ and $\xi_s$, on the [Objective](objective.md) page. They follow the paper that introduced them.

Superscripts only say what role a symbol plays, never a limit: *ch* and *dis* (charge, discharge), *buy* and *sell*, *start* and *stop*, *up* and *down*, *net*, *adj* (adjustment), *trip*, *trade*, *fix* (fixed), *init* and *final* (the run's initial and final conditions), *var* (variable), *deg* (degradation) and *val* (value).

Each page ends with a table that maps its symbols to the odys attributes they come from, with units.

## Sign convention

Every asset and market connects to one bus, and power **into** the bus counts as positive. So supply is positive and demand is negative:

| Who | Injects into the bus |
| --- | -------------------- |
| A generator | $+p_{g,s,t}$ |
| A battery | $+p^{dis}_{k,s,t} - p^{ch}_{k,s,t}$ (discharging minus charging) |
| A market | $+p^{buy}_{m,s,t} - p^{sell}_{m,s,t}$ (buying minus selling) |
| A fixed load | $-D_{l,s,t}$ |
| A flexible load | $-(D_{l,s,t} + p^{adj}_{l,s,t})$ |

One exception to keep in mind: a battery's **net power** $p^{net}_{k,s,t} = p^{ch}_{k,s,t} - p^{dis}_{k,s,t}$ is positive while it *charges*. That's the battery's own point of view, and it's what the results report as `net_power`.

The optimizer **maximizes** profit. Costs enter the profit with a minus sign, and revenues with a plus sign.

## Time and boundary conventions

odys cuts the run into $T$ steps of equal length. $\Delta t$ is the length of one step in hours (`timestep`), so a step of 15 minutes has $\Delta t = 0.25$. Within a step, power is constant. The energy of a step is power times $\Delta t$: 10 MW for a 15-minute step is 2.5 MWh.

States describe the **end** of a step. $\mathrm{soc}_{k,s,t}$ is the state of charge once step $t$ is over:

```text
  soc_init        soc_0        soc_1                soc_{T-1}
     |   step 0     |   step 1   |   ...   | step T-1 |
     ^                                                ^
  initial condition                     final condition, if set
```

The run's boundary conditions fill in what lies outside the horizon:

- **Before step 0**, the initial conditions stand in for "the previous step". A generator's previous output is its initial output $P^{init}_g$, it was on if $P^{init}_g > 0$, and it had been in that state for $N^{init}_g$ steps. A battery starts from $\mathrm{soc}^{init}_k$.
- **After step $T - 1$**, a final condition, when you set one, is an equality: the generator's output at the last step is exactly $P^{final}_g$, and the battery's state of charge is exactly $\mathrm{soc}^{final}_k$. Without a final condition, the last step is free.
- The initial and final conditions are the same in every scenario.

Durations become whole numbers of steps: minimum up and down times, a generator's time in its initial state, and trip departures and returns. odys rejects a duration that doesn't fit the step length. With 15-minute steps, a 2-hour minimum up time is 8 steps, and a 10-minute one is refused.

A battery loses a share $\delta_k$ of its charge per hour (`self_discharge_rate`), applied to the state of charge of the previous step as $(1 - \delta_k \Delta t)$. With $\delta_k = 0.01$ and hourly steps, a full battery keeps 99 % of its charge from one step to the next.

## Initial-condition defaults

You don't always have to say where an asset starts:

| Asset | Without an initial condition |
| ----- | ---------------------------- |
| Generator | Starts off ($P^{init}_g = 0$), as if it had been off forever ($N^{init}_g = \infty$), so no minimum time carries over. odys asks for a `GeneratorInitialState` as soon as the start matters: when `ramp_up`, `ramp_down`, `min_up_time`, `min_down_time`, `startup_cost` or `shutdown_cost` is set. |
| Generator with an initial state but no `time_in_state` | As if it had been in that state forever ($N^{init}_g = \infty$). odys only allows this when the matching minimum time is unset. |
| Stationary storage, electric vehicle | No default: a `StorageInitialState` or `ElectricVehicleInitialState` is always required, because the charge carries over from step to step. |

Final conditions are always optional.

## Scenarios and decision stages

A scenario is one possible future: its prices, demand and available capacity. Scenario $s$ happens with probability $\pi_s$, and the probabilities add up to 1.

Most decisions adapt to each scenario, as if the optimizer knew which future will happen. The only exceptions are the trades on stage-fixed markets: they are decided once ([non-anticipativity](non_anticipativity.md)), before the future is known, and are the same in every scenario. That's the reading rule from above at work: a symbol with $s$ can differ between scenarios, and one without $s$ cannot.

With a single scenario, $\pi_s = 1$, and every equation in this section is the plain deterministic model. There is no separate deterministic version to read.

The first symbol you'll meet everywhere is $s$. Where does it come from? See [Scenarios](scenarios.md).
