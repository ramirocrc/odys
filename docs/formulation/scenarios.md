---
icon: lucide/git-branch
---

# Scenario structure

<!-- Hook: When are decisions made, and which ones wait for the future? -->

<!-- Scope: how scenarios enter the model, which decisions are shared across them, and when they interact. Motivation stays on the User Guide's Stochastic optimization page (link). -->

## Scenarios and probabilities

<!-- 𝒮, π_s, Σ π_s = 1; conditions identical in every scenario. -->

## First- and second-stage decisions

<!-- Two-stage stochastic program with recourse. First stage: sell, buy and trade_mode of markets with stage_fixed=True. Everything else is second stage. -->

## NA-1 · Stage-fixed trades are the same in every scenario {#na-1}

<!-- Per-scenario copies tied to the first scenario s₀, ∀ m ∈ ℳ^fix, s ∈ 𝒮, t ∈ 𝒯. Equivalent to one shared variable; why the code uses copies. Model names: non_anticipativity_market_{sell_volume,buy_volume,trade_mode}_constraint. -->

## When scenarios decouple

<!-- Coupled only through NA-1 and CVaR. Caveats: π_s = 0, every scenario must be feasible, MIP gap is global. -->

## Where to find each symbol in odys

<!-- Visible table: Symbol | Attribute | Type (Parameter, Variable, Result) | Unit -->

<!-- Bridge: Decisions are made for something. What is odys chasing? → [Objective](objective.md) -->

---

Implemented in [`odys.optimization.formulations.energy_market`](../developer/api/optimization/formulations/energy_market.md) (non-anticipativity) and [`odys.domain.scenario`](../developer/api/domain/scenario.md).
