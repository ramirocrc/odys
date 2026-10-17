---
icon: lucide/book-open
---

# Notation and conventions

<!-- Hook: How do I read the symbols? Skim it now, come back whenever a symbol is unclear. -->

<!-- Scope: the reference for every symbol and convention used in this section. Each symbol has exactly one meaning. -->

## Sets and indices

<!-- 𝒯, 𝒮, 𝒢, ℬ, ℰ, 𝒦 = ℬ ∪ ℰ, 𝒞, ℒ, ℒ^fix, ℳ, ℳ^fix; indices t, s, g, b, e, k, c, l, m. Index order: asset, scenario, time. τ only inside min up/down windows. -->

## Symbol convention

<!-- Variables lowercase Latin, parameters uppercase Latin, costs lowercase c, rates/efficiencies/prices/probabilities Greek, bounds with bars, superscripts for roles only. -->

## Sign convention

<!-- Injection into the bus is positive (supply). p^net = p^ch − p^dis (positive = charging). Objective is maximized. -->

## Time and boundary conventions

<!-- 𝒯 = {0, …, T−1}, Δt in hours, end-of-step states, soc_start before step 0, soc_end at the end of step T−1 (equality), t−1 quantities at t = 0 come from the initial conditions, self-discharge (1 − δΔt). Timeline figure. -->

## Initial-condition defaults

<!-- Generator without GeneratorInitialState: off, steps_in_state = ∞. Without time_in_state: ∞. Battery initial SoC: always required. -->

## Scenarios and decision stages

<!-- Short framing: scenario = one realization with π_s ∈ [0, 1]; only stage-fixed market variables are first-stage; reading rule for symbols with and without s; deterministic case |𝒮| = 1. Links to Scenario structure. -->

<!-- Bridge: The first symbol you'll meet everywhere is s. Where does it come from? → [Scenario structure](scenarios.md) -->
