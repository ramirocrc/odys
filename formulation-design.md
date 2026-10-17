# Odys docs — "Mathematical Formulation" section: design

## Context
Right now the Odys formulation is spread across the User Guide. Asset pages (e.g. `user_guide/assets/stationary_storage.md`) mix usage, field tables, equations and symbol→attribute tables. `user_guide/mathematical_notation.md` is a long glossary: the power balance is described only in words, CVaR and non-anticipativity are never written out, and Δt and the time conventions are undefined. The goal is a dedicated section modelled on PyPSA's optimization docs (one page per model part, display equations, mapping tables), plus the two things papers have and PyPSA lacks: an explicit list of modelling assumptions and a numbered compact model.

This document is the design brief for the rewrite. It does not edit the odys repo itself.

## Decisions (from Q&A)
| Topic | Decision |
|---|---|
| Audience | Modelers who **audit assumptions** and **interpret results**. No publication planned: this is a software reference. |
| Voice | Friendly and light, for human readers, not a research paper. All text visible, no running example, reference page order. Voice rules: `write-docs` skill §13; storyline: "Voice and storyline" below. |
| Explanation depth | Precise reference **plus rationale**. Each constraint says what it enforces, why it takes this form (intuition, not derivation), and what it does **not** model. The goal is that readers can trust the framework. |
| Page split | By model part (see outline below). "Overview" and "Notation & conventions" are **two pages**: auditors read the first, then come back to the second as a reference. |
| Battery math | Written **once**, over k ∈ 𝒦 = ℬ ∪ ℰ, on the Batteries page (the code shares one `StorageFormulation`). The EV page writes only what EVs add. |
| Code issues | Pages **document the code as it is**. Known problems are tracked in GitHub issues (#124, #140–#145, see "Open code issues"). Each issue's fix also updates the formulation pages. |
| Asset pages | Equations move out. User Guide keeps usage, fields, examples and results, and links to the formulation pages. **Requires updating the `write-docs` skill (§4 and its page templates)**, which currently put a "Mathematical formulation" section at the end of every asset page. |
| Scenarios | General form throughout: every equation carries `s`. Deterministic = \|𝒮\| = 1. Introduced up front (Overview + Scenario structure page). |
| Stochastic structure | **Two-stage stochastic program with recourse.** No rolling horizon or scenario tree exists. ROADMAP's "multi-stage" means stage-fixed markets. |
| Symbol ↔ code | A visible table per page: Symbol \| Attribute \| Type \| Unit. Constraints also show their linopy name. |
| Depth | Variable domains and bounds, the exact big-M / linearizations, add/bind conditions, hidden constants, limitations. **Not** planned features. |
| Notation | Redesign allowed (convention below) |
| Traceability | "Implemented in" footer per page, linking to the API Reference. Linopy constraint name per constraint. |
| Objective sense | **Maximize** (checked: `domain/objective.py`, `model_builder.py` `sense="max"`) |
| Contributor template | Not needed |

## Section outline
```
Mathematical Formulation/
├── Overview                problem class & size, modelling assumptions, guaranteed by validation, compact numbered model
├── Notation & conventions  sets, index rules, symbol convention, sign convention, time & boundary conventions (timeline),
│                           initial-condition defaults
├── Scenario structure      𝒮, π_s, two-stage view, first- vs second-stage variables, non-anticipativity written out,
│                           when scenarios decouple
├── Objective               Π_s defined once; expected profit; CVaR (Rockafellar–Uryasev) with ζ, ξ_s, α; weights w^P, w^C
├── Power balance           single bus, hard equality ∀ s,t, no slack; fixed loads (D^fix) live here
├── Markets                 buy/sell limits, trade-mode binary, trade direction, stage-fixed (links to Scenario structure)
├── Generators              limits, ε-status, commitment, start-up/shut-down, ramping, min up/down times, final power, costs
├── Batteries               k ∈ ℬ ∪ ℰ: SOC dynamics (start, interior, end), bounds, charge/discharge mode binary (big-M),
│                           degradation; trip term is 0 for stationary storage
├── EVs & chargers          only the additions: trip energy, driving, departure SoC, charger assignment & power cap
└── Flexible loads          adjustment bounds, value of consumption
```
Markets come right after the power balance: their variables are in the balance, and they hold the only first-stage variables, so they follow the Scenario structure page naturally. There is no Multi-stage page and no fixed-load page. The old `user_guide/mathematical_notation.md` page is deleted and its content moves to "Notation & conventions". No redirects and no stub pages: the section is written fresh, and old URLs are not maintained.

## Overview: required content

### Problem class and size
State that the model is a MILP. List the binaries, with counts in terms of |𝒮|, |𝒯| and the asset sets, so readers can judge solve times:
- Generators: u, y^start, y^stop, 3·|𝒢|·|𝒮|·|𝒯| in total. The three-constraint start-up/shut-down logic fixes y^start and y^stop exactly from u, so only u carries real combinatorial choice. Say so.
- Batteries: mode z, (|ℬ|+|ℰ|)·|𝒮|·|𝒯|.
- Markets: trade mode, |ℳ|·|𝒮|·|𝒯| (#140).
- Chargers: assignment a, |𝒞|·|ℰ|·|𝒮|·|𝒯|.
- CVaR adds only continuous variables (ζ scalar, ξ_s per scenario).

### Modelling assumptions
Audit readers check this list first, so each item links to the constraint that implements it:
- Single bus ("copper plate"): no network, no losses except battery efficiencies.
- The power balance is a hard equality with no slack or unserved energy, so an imbalance makes the problem infeasible.
- Discrete time with a constant Δt. Power is constant within a step, and state variables are end-of-step values.
- Price-taker: prices are exogenous. A market is limited only by its per-step volume cap and its allowed trade direction. Buying and selling use the same price, with no fees or spread.
- Linear costs: a constant variable cost per MWh, **no no-load cost** (u has no running cost), and start-up/shut-down costs that don't depend on how long the unit was off or on. Degradation is linear in throughput `(p^{ch}+p^{dis})Δt` (no depth-of-discharge or calendar aging).
- Ramp limits are in **MW per step** and don't scale with Δt (#124). Ramping also applies at start-up and shut-down; there are no separate SU/SD ramp limits.
- Final conditions are **equalities** (`soc_end`, generator final power). There is no terminal value of stored energy: without `soc_end`, the optimizer empties batteries by the end of the horizon whenever that pays.
- Charger assignment can switch every step at no cost (no plug-in/plug-out constraint).
- Perfect foresight within each scenario. Only stage-fixed market positions are first-stage. Generator commitment is second-stage.
- Without a stage-fixed market and without CVaR, the scenarios **decouple**, and the result equals solving each scenario on its own. Caveats: a scenario with π_s = 0 (allowed) gets any feasible plan; every scenario must be feasible; the MIP gap applies to the whole problem, not per scenario.
- odys reports no duals or marginal prices (in a MILP they exist only for the LP with the binaries fixed).
- Parameters that exist but are not used in the formulation: `Charger.efficiency`.

### Guaranteed by validation, not by constraints
Some properties hold because `EnergySystem` rejects inputs that would break them, not because a constraint enforces them. List them so auditors don't look for the missing constraint:
- Actual flexible load ≥ 0: base profile ≥ `max_decrease` and the bounds are consistent (`domain/profiles.py`, `LoadProfile` validator).
- Available capacity ≤ `nominal_power` (`AvailableCapacityProfile` validator).
- A trip departing at t = 0 is feasible from the initial SoC (`ElectricVehicleInitialState` validators). The departure-SoC constraint does not cover that trip, see EVs.
- Trips don't overlap (`ElectricVehicle`). Trip times, `min_up_time`, `min_down_time` and `time_in_state` are whole numbers of steps.
- Initial and final generator power is 0 or within [`min_power`, `nominal_power`]. Final power ≤ available capacity at the last step. Initial/final SoC is within [`soc_min`, `soc_max`].
- Σ_s π_s = 1. Chargers exist if and only if EVs exist (`AssetPortfolio`).
- A generator's initial state is required whenever ramping, min up/down times or start-up/shut-down costs make the result depend on it.

### Compact numbered model
`max (objective) s.t. (PB-1), (M-…), (NA-…), (G-1…G-n), (B-1…), (EV-…), (CH-…), (FL-…), (CV-…), x ∈ X`. Every reference links to its page.

## Notation & conventions: required content

### Time and boundary conventions (with a small timeline figure)
- 𝒯 = {0, …, T−1} (the code is 0-based). Δt = `timestep` in hours (`ModelContext.timestep_hours`), defined once.
- `soc_t` is the state at the **end** of step t. `soc_start` is the state before step 0. `soc_end` fixes the state at the end of step T−1 (equality, `*_soc_end_constraint`, only where set).
- At t = 0, "t−1" quantities come from the initial conditions: `initial_power`, the initial status (on ⇔ initial power > 0) and the steps already spent in that state.
- Defaults without a `GeneratorInitialState`: off (power 0), and "in that state for longer than any minimum time" (`steps_in_state = ∞`, nothing carries over). Without `time_in_state`, the same ∞ applies (validation only allows that when the matching minimum time is unset). Battery initial SoC has no default: it is always required.
- Self-discharge is applied as `(1 − δΔt)` to the previous SOC (a linear approximation of exponential decay, δ per hour).

### Scenarios and decision stages (short framing, no derivations)
- A scenario is one realization of the uncertain inputs (prices, demand, available capacity), with probability π_s ∈ [0, 1] and Σ_s π_s = 1. Initial and final conditions are the same in every scenario.
- Two-stage structure: first-stage decisions are fixed before uncertainty is revealed. **Only stage-fixed market variables are first-stage.** Everything else adapts per scenario.
- Reading rule: a symbol indexed by `s` may differ across scenarios. A symbol without `s` is shared by all scenarios.
- Deterministic case: |𝒮| = 1, π = 1. Every equation reduces to the deterministic model, so no separate deterministic version is written.

## Scenario structure: required content
- The scenario set, probabilities and the two-stage view.
- The first-stage variables are `sell`, `buy` **and the `trade_mode` binary** of markets with `stage_fixed=True`. Generator commitment, storage, EV charging and charger assignment are second-stage.
- Non-anticipativity, as implemented: per-scenario copies tied to the first scenario s₀ (the first in `ScenarioSet` order), `x_{m,s,t} = x_{m,s₀,t}  ∀ m ∈ ℳ^{fix}, s ∈ 𝒮, t ∈ 𝒯` (the row for s₀ is trivial; the code adds it). Say that this is equivalent to a single shared variable, and why the code uses copies (every variable keeps the same (s, t, asset) shape). Names: `non_anticipativity_market_{sell_volume,buy_volume,trade_mode}_constraint`.
- Scenarios are coupled **only** through non-anticipativity and CVaR.
- Motivation ("why use scenarios") stays on the User Guide's Stochastic Optimization page, which this page links to.

## Objective: required content
- Per-scenario profit, defined once:
  Π_s = market revenue `Σ (p^{sell} − p^{buy})·λ·Δt` − generator cost (variable `c^{var}·p·Δt` + start-up + shut-down) − battery degradation `c^{deg}·(p^{ch}+p^{dis})·Δt` + flexible-load value of the **adjustment** `c^{val}·p^{adj}·Δt`. Fixed loads add nothing. Each asset page's "Objective contribution" refers to its term in this sum.
- Interpretation note: the value of the flexible loads' base consumption is a constant and is left out, so the objective value is not total welfare or total cost.
- Objective: `max  w^P · Σ_s π_s Π_s  +  w^C · ( ζ − 1/(1−α) · Σ_s π_s ξ_s )`, with `ξ_s ≥ ζ − Π_s` (`cvar_shortfall_constraint`), `ξ_s ≥ 0`, ζ free.
- CVaR is Rockafellar–Uryasev (2000) on the **lower tail of profit**, with α the confidence level (`CVaRTerm.confidence_level` ∈ (0, 1)).
- The weights are two independent non-negative numbers, not a convex `(1−λ)/λ` split, and they are not normalized, so `w^C` also rescales the objective. `ProfitTerm` is mandatory. `CVaRTerm` is optional.
- Explain what ζ means at the optimum: the (1−α)-quantile of Π (VaR), the profit level with probability mass 1−α at or below it. With discrete scenarios the optimal ζ can be a whole interval, and the solver returns one point of it.
- Edge case: with `w^P = 0`, scenarios outside the tail don't affect the objective, so their plans are any feasible plan.

## Voice and storyline
The section is for human readers, so it should read like a friendly guide, not a research paper. The page order stays the reference order, there is no running example, and **all text stays visible** (no collapsed blocks). The storyline comes from how pages open, connect and explain.

### Storyline
Each page answers the question the previous page leaves open, and ends with a one-line bridge to the next page:

| Page | Question it answers | Bridge to the next page |
|---|---|---|
| Overview | What does odys actually solve? | "Before the equations, a few words on how we write them." |
| Notation | How do I read the symbols? | "The first symbol you'll meet everywhere is *s*. Where does it come from?" |
| Scenarios | When are decisions made, and which ones wait for the future? | "Decisions are made *for* something. What is odys chasing?" |
| Objective | What counts as a good plan? | "Profit is earned on energy, and energy has to add up at every step." |
| Power balance | What ties every asset together? | "Who fills the gap? First, the outside world." |
| Markets | How do I buy and sell? | "Buying isn't the only option: you can make your own power." |
| Generators | How do I make my own power? | "Power made now is used now, unless you can store it." |
| Batteries | How do I move energy in time? | "Some batteries drive away." |
| EVs & chargers | What changes when the battery leaves? | "Last piece: demand that can bend." |
| Flexible loads | How can demand adapt? | Back to the Overview's full model: "You've now seen every piece." |

### The Overview opens with a hook, not a definition
- Open with the question odys answers in every run, in everyday words: "You own a few assets, you can trade on a few markets, and you don't know exactly what tomorrow brings. What should each asset do at every step?"
- One picture: assets and markets around a single bus. The arrows are the power balance terms.
- "How to read this section": a short tour paragraph that follows the storyline table.
- Friendly headings: "What odys assumes (and what it doesn't)", "Checked before solving", "The whole model on one screen".

### Voice and page template
The voice rules are in the `write-docs` skill (`.agents/skills/write-docs/SKILL.md`) §13. The constraint rhythm is in §4, and the page layout is in its `templates.md`. This brief does not repeat them.

### Rationale to write (checked against the code, 2026-10-17)
- **Battery mode binary.** With η < 1, charging and discharging at the same time burns energy. The optimizer would do that whenever surplus energy has no other outlet: negative prices, or a generator stuck at `min_power`. The balance has no curtailment variable, so this case is real. The binary rules it out. MILP form: `p^{ch} ≤ z·\overline{P}^{ch}`, `p^{dis} ≤ (1−z)·\overline{P}^{dis}`.
- **Generator `p ≥ 10⁻⁵·P·u`** (`generator_status_constraint`). Without it, the optimizer could keep `u = 1` at zero output and avoid start-up costs and min-down-time limits for free. It binds only when `min_power < 10⁻⁵·P` (in practice `min_power = 0`), and it makes `status = 1` mean "producing" in results. Document it as a hidden constant that users can't set.
- **Ramping applies at start-up and shut-down too**, starting from `initial_power` at t = 0. A unit with `min_power > ramp_up` can never start, and one with output above `ramp_down` can't shut down in one step. **Resolved: document it as a limitation** (already in `generator.md`). Papers usually add separate SU/SD ramp limits. Units: MW per step (#124).
- **Market `trade_mode` binary.** Each market has one price per (s, t), so buying and selling the same amount nets to zero in both the balance and the profit. The binary only removes a solution with the same payoff, at a cost of |ℳ|·|𝒮|·|𝒯| binaries, which are non-anticipative on stage-fixed markets. Document it as such (#140). MILP form: `p^{sell} ≤ y·V`, `p^{buy} ≤ (1−y)·V`, with V = `max_trading_volume_per_step`.
- **Min up/down time.** Code form, per generator g with window L = `min_up_steps`: `Σ_{τ=t−L+1}^{t} u_τ + min(L−1−t, k_g)⁺ ≥ L·y^{stop}_{t+1}`, where k_g = steps already on before the horizon (0 if initially off). The y^{stop}_{t+1} at the last step is 0. A shutdown at t = 0 is handled separately by `generator_initial_min_uptime_constraint` (y^{stop}_0 = 0 when initially on for fewer than L steps). Down time is symmetric with `1 − u` and y^{start}. Verified: linopy's rolling sum over a partial window sums only the existing steps (linopy 0.10.0). **Equivalence argument** for integer points: a shutdown at t+1 requires the L steps ending at t to be on, which is the same as no start-up in (t−L+1, t], i.e. Rajan–Takriti. It is weaker in the LP relaxation (#141). Always added; binds only when the minimum time is more than one step (the default is 1 step).
- **Chargers.** The cap applies to `p^{ch} + p^{dis}` combined: `p^{ch}_{e} + p^{dis}_{e} ≤ Σ_c a_{c,e}·P_c`. With no charger assigned the cap is 0, so a vehicle charges or discharges only through an assigned charger. Each charger serves at most one vehicle and each vehicle uses at most one charger. The charger efficiency field exists but **isn't used**. The result `ChargerDispatch.power` counts charging only, not V2G (#142).
- **EV trips.** Trip energy is spread evenly over the trip's steps and subtracted from SOC as a fraction of capacity: `E^{trip}_{e,t} / E_e`. The departure SoC is enforced at the end of the step **before** departure (`ev_min_soc_departure_constraint`). For a trip departing at t = 0 there is no such step, so validation covers it instead.
- **Flexible loads.** `p^{adj}` is free. Lower bound: `min_load − D` if `min_load` is set, else `−max_decrease`. Upper bound: `max_load − D` if set, else `max_increase` (absolute bounds override relative ones).
- **Available capacity** (`available_capacity_constraint`): `p ≤ A_{g,s,t}`, always added, with +∞ when the scenario has no profile. It does not multiply u.
- **Redundant constraints.** `*_capacity_constraint` (soc ≤ 1, implied by `soc_max ≤ 1`, #143). `market_max_{sell,buy}_volume_constraint` (implied by the trade-mode pair, #144). `ev_driving_constraint` (implied by the charger constraints, #145).

## Notation convention
- **Sets**: calligraphic. 𝒯 (timesteps), 𝒮 (scenarios), 𝒢 (generators), ℬ (stationary storages), ℰ (EVs), 𝒦 = ℬ ∪ ℰ (batteries), 𝒞 (chargers), ℒ (flexible loads), ℒ^{fix} (fixed loads), ℳ (markets), ℳ^{fix} ⊆ ℳ (stage-fixed markets). Indices are the lowercase letters t, s, g, b, e, k, c, l, m.
- **Index order**: asset, scenario, time, e.g. `p^{ch}_{k,s,t}`. The current docs use `p_{g,t,s}` and the code uses (s, t, asset), so rewrite the existing pages consistently.
- **Decision variables**: lowercase Latin. `p` = power, including market trades (`p^{buy}_{m,s,t}`, `p^{sell}_{m,s,t}`), because `max_trading_volume_per_step` is in MW and the power balance then uses power symbols throughout, and the flexible-load adjustment `p^{adj}_{l,s,t}`. `\mathrm{soc}` = state of charge **as a fraction of capacity** (∈ [0,1]; the code divides by capacity and enforces `soc ≤ 1`). `u` = commitment, `y^{start}`, `y^{stop}`, `z` = battery mode binary, `y^{trade}_{m,s,t}` = market trade mode (avoid a second `z`), `a_{c,e,s,t}` = charger assignment, `ξ_s` (CVaR shortfall), `ζ` (VaR threshold; replaces the current `η` to avoid clashing with efficiency).
- **Parameters**: uppercase Latin for capacities and profiles (`E_k`, `D_{l,s,t}`, `A_{g,s,t}`, `E^{trip}_{e,t}`, `V_m`). Bounds use over/underlines (`\overline{P}^{ch}_k`, `\underline{\mathrm{soc}}_k`). Lowercase `c` for costs (`c^{deg}_k`, `c^{start}_g`, `c^{val}_l`). Greek for rates, efficiencies, prices and probabilities (`η^{ch}`, `δ`, `λ_{m,s,t}`, `π_s`, `α`). Objective weights are `w^P` and `w^C`.
- **Superscripts**: roles only (ch, dis, buy, sell, start, stop, up, down, net, fix, adj, trip, trade). Bounds use bars, not `max`/`min` superscripts.
- **τ** is reserved for the summation index inside min up/down windows. It is never a horizon.
- **Signs**: power injection into the bus is positive (supply). State `p^{net} = p^{ch} − p^{dis}` (positive = charging, the opposite of the injection sign) and the objective sense once, in Notation & conventions.
- Each symbol has exactly one meaning across all pages. No reuse like PyPSA's `n`.

## Tooling notes (Zensical, Material-compatible Markdown)
- Math via `pymdownx.arithmatex` (`generic = true`) + MathJax 3 from the CDN, loaded **with no config script**. `\tag{B-3}` works for display labels, but `\eqref` does not work across pages and auto-numbering is off. Use heading anchors (`### SOC dynamics {#b-3}`) for references, which also matches "one H3 per constraint".
- Check that MathJax re-typesets after instant navigation, if that feature is enabled.
- Tabs are not needed, because scenarios use the general form throughout.

## Resolved against the code (odys HEAD, 2026-10-17)
- Objective sense: maximize. Composition: `w^P·E[Π] + w^C·CVaR_α(Π)`, with independent weights.
- SOC: a fraction of capacity, end-of-step.
- `soc_end` exists (`*_soc_end_constraint`, last step, equality, only where set). The first step is handled by `*_soc_start_constraint`; interior steps by `*_soc_dynamics_constraint` (t ≥ 1).
- Battery mode binary: `p^{ch} ≤ z·\overline{P}^{ch}` and `p^{dis} ≤ (1−z)·\overline{P}^{dis}` (big-M = the power ratings). Market trade mode: the same pattern with M = `max_trading_volume_per_step` (always finite, `> 0`).
- First-stage variables: stage-fixed market `sell`, `buy` and `trade_mode`, tied to the first scenario.
- τ: the min up/down window index, not a rolling horizon.
- Min up/down: equivalent to the standard form on integer points (argument above), weaker LP relaxation.
- Ramping at start-up/shut-down: a documented limitation.
- Add/bind conditions:

  | Constraint | Added | Binding when |
  |---|---|---|
  | `generator_max_ramp_{up,down}_constraint` | always | `ramp_up` / `ramp_down` set (default `nominal_power`) |
  | `generator_min_{uptime,downtime}_{name}_constraint` | always, one per generator | minimum time > 1 step |
  | `generator_initial_min_{uptime,downtime}_constraint` | only if some generator is still within its minimum time at t = 0 | always, when added |
  | `generator_final_power_constraint` | only for generators with a `GeneratorFinalState` | always, when added |
  | `available_capacity_constraint` | always | the scenario has an `AvailableCapacityProfile` (default +∞) |
  | `flexible_load_adjustment_{lower,upper}_bound_constraint` | always | always |
  | `ev_min_soc_departure_constraint` | always (0 outside departures) | the step before a trip departs |
  | `market_buy_only_constraint` / `market_sell_only_constraint` | always (empty when no market restricts direction) | the market's `allowed_trade_direction` |
  | `non_anticipativity_market_*_constraint` | always (empty without stage-fixed markets) | `stage_fixed=True` |
  | `cvar_shortfall_constraint` | only with a `CVaRTerm` | always, when added |
- Exact linopy names that break the `<asset>_` prefix pattern: the variable `load_adjustment` and `available_capacity_constraint`. The consistency test must use exact names.

## Open code issues (document as-is; each fix also updates the formulation pages)
- #124: ramp limits ignore Δt (applied per step).
- #140: market `trade_mode` only removes payoff-equivalent solutions.
- #141: min up/down → Rajan–Takriti form (tighter, vectorized).
- #142: `ChargerDispatch.power` leaves out V2G discharge.
- #143: redundant `*_capacity_constraint`.
- #144: redundant `market_max_{sell,buy}_volume_constraint` (depends on #140).
- #145: redundant `ev_driving_constraint`.

## Still to check while drafting
- The full mapping of every symbol to its attribute and result path (build each row from the real class; result names are in `results/dispatch.py`).

## Verification (for the later rewrite)
- `zensical build` (or `serve`) renders all math and tables without warnings, and the nav matches the outline.
- No links point to `mathematical_notation.md` or to the removed `#math-*` anchors on asset pages (grep `docs/`, `README.md` and docstrings); `--strict` catches the rest.
- Every symbol in every page appears in that page's mapping table, with a unit. Every attribute exists in the API Reference.
- No equations remain in `docs/user_guide/` (grep for `$$`; today that includes `concepts/power_balance.md`, `optimization/objective.md` and `optimization/stochastic.md` besides the asset and market pages). The developer API pages keep their docstring math. Each asset page links to its formulation page. The `write-docs` skill (§4, information architecture, templates) matches the new layout.
- **A docs/model consistency test**, in the spirit of `tests/test_architecture_docs.py`. Build a model that includes every asset type, a stage-fixed market, a generator still within its minimum time at t = 0, final conditions and a CVaR term (so every conditional constraint is added), then check that every `model.constraints` / `model.variables` name appears in the formulation pages, and that every documented name exists in the model. Per-generator names (`generator_min_uptime_{name}_constraint`) need a pattern match.
