---
icon: lucide/target
---

# Objective

<!-- Hook: What counts as a good plan? -->

<!-- Scope: what odys maximizes. Π_s is defined once here; every asset page's "Objective contribution" refers to its term. -->

## Profit per scenario

<!-- Π_s = market revenue − generator cost − battery degradation + flexible-load value of the adjustment. Fixed loads add nothing. Base consumption value is left out, so the objective is not total welfare. -->

## Expected profit

<!-- w^P · Σ_s π_s Π_s. ProfitTerm is mandatory. -->

## Conditional value at risk

<!-- Rockafellar–Uryasev on the lower tail of profit: ζ − 1/(1−α) Σ_s π_s ξ_s. Meaning of ζ at the optimum (the (1−α)-quantile, possibly an interval). -->

### CV-1 · Each scenario's shortfall below the threshold {#cv-1}

<!-- ξ_s ≥ ζ − Π_s, ξ_s ≥ 0, ζ free. Model name: cvar_shortfall_constraint. Added only with a CVaRTerm. -->

## Combined objective

<!-- max w^P · E[Π] + w^C · CVaR_α(Π). Independent, non-normalized weights; edge case w^P = 0. -->

## Where to find each symbol in odys

<!-- Visible table: Symbol | Attribute | Type (Parameter, Variable, Result) | Unit -->

<!-- Bridge: Profit is earned on energy, and energy has to add up at every step. → [Power balance](power_balance.md) -->

---

Implemented in [`odys.optimization.objective_terms`](../developer/api/optimization/objective_terms/index.md) ([`profit`](../developer/api/optimization/objective_terms/profit.md), [`cvar`](../developer/api/optimization/objective_terms/cvar.md)).
