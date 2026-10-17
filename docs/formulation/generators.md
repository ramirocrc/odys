---
icon: lucide/factory
---

# Generators

<!-- Hook: How do I make my own power? -->

<!-- Scope: added for every Generator. Each constraint: plain sentence, equation (logical then MILP form for binaries), read aloud, why it looks like this, good to know, facts line (Added · Binds · Name). -->

## Sets and indices

## Variables

<!-- p ≥ 0; u, y^start, y^stop ∈ {0, 1}. -->

## Constraints

### G-1 · Output never exceeds the rating {#g-1}

<!-- generator_max_power_constraint. -->

### G-2 · On means producing {#g-2}

<!-- generator_status_constraint, hidden constant 1e-5. -->

### G-3 · When on, output stays above the minimum {#g-3}

<!-- generator_min_power_constraint. -->

### G-4 · Output fits the available capacity {#g-4}

<!-- available_capacity_constraint (+∞ without a profile, not multiplied by u). -->

### G-5 · Start-ups are counted {#g-5}

<!-- generator_startup_{lower_bound,upper_bound_1,upper_bound_2}_constraint. -->

### G-6 · Shut-downs are counted {#g-6}

<!-- generator_shutdown_{lower_bound,upper_bound_1,upper_bound_2}_constraint. -->

### G-7 · Output changes gradually {#g-7}

<!-- generator_max_ramp_{up,down}_constraint. MW per step (#124); applies at start-up and shut-down. -->

### G-8 · Once started, a unit stays on for a while {#g-8}

<!-- generator_min_uptime_{name}_constraint, generator_initial_min_uptime_constraint. Equivalence argument; weaker LP relaxation (#141). -->

### G-9 · Once stopped, a unit stays off for a while {#g-9}

<!-- generator_min_downtime_{name}_constraint, generator_initial_min_downtime_constraint. -->

### G-10 · The last step hits the final output {#g-10}

<!-- generator_final_power_constraint, only with a GeneratorFinalState. -->

## Power balance contribution

## Objective contribution

## Where to find each symbol in odys

<!-- Visible table: Symbol | Attribute | Type (Parameter, Variable, Result) | Unit -->

<!-- Bridge: Power made now is used now, unless you can store it. → [Batteries](batteries.md) -->

---

Implemented in [`odys.optimization.formulations.generator`](../developer/api/optimization/formulations/generator.md).
