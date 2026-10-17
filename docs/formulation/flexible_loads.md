---
icon: lucide/sliders-horizontal
---

# Flexible loads

<!-- Hook: How can demand adapt? -->

<!-- Scope: added for every FlexibleLoad. Each constraint: plain sentence, equation (logical then MILP form for binaries), read aloud, why it looks like this, good to know, facts line (Added · Binds · Name). -->

## Sets and indices

## Variables

<!-- p^adj free (linopy name: load_adjustment). -->

## Constraints

### FL-1 · Demand can drop, but only so far {#fl-1}

<!-- flexible_load_adjustment_lower_bound_constraint: min_load − D if set, else −max_decrease. -->

### FL-2 · Demand can rise, but only so far {#fl-2}

<!-- flexible_load_adjustment_upper_bound_constraint: max_load − D if set, else max_increase. -->

## Power balance contribution

## Objective contribution

<!-- c^val · p^adj · Δt: only the adjustment is valued. -->

## Where to find each symbol in odys

<!-- Visible table: Symbol | Attribute | Type (Parameter, Variable, Result) | Unit -->

<!-- Bridge: You've now seen every piece. Back to the whole model on one screen. → [Overview](index.md#the-whole-model-on-one-screen) -->

---

Implemented in [`odys.optimization.formulations.flexible_load`](../developer/api/optimization/formulations/flexible_load.md).
