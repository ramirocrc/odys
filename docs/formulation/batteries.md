---
icon: lucide/battery-medium
---

# Batteries

<!-- Hook: How do I move energy in time? -->

<!-- Scope: the battery model shared by stationary storage and electric vehicles, written once over k ∈ 𝒦 = ℬ ∪ ℰ. The trip term is 0 for stationary storage; EVs & chargers adds the rest. Model names are prefixed with stationary_storage_ or ev_. Each constraint: plain sentence, equation (logical then MILP form for binaries), read aloud, why it looks like this, good to know, facts line (Added · Binds · Name). -->

## Sets and indices

## Variables

<!-- p^ch, p^dis ≥ 0; p^net free; soc ≥ 0; z ∈ {0, 1}. -->

## Constraints

### B-1 · Charging stays within the rating, in charging mode {#b-1}

<!-- *_max_charge_constraint. -->

### B-2 · Discharging stays within the rating, outside charging mode {#b-2}

<!-- *_max_discharge_constraint. -->

### B-3 · The first step starts from the initial charge {#b-3}

<!-- *_soc_start_constraint. -->

### B-4 · Charge carries over from step to step {#b-4}

<!-- *_soc_dynamics_constraint, t ≥ 1. -->

### B-5 · The last step hits the final charge {#b-5}

<!-- *_soc_end_constraint, equality, only where set. -->

### B-6 · Charge stays between its limits {#b-6}

<!-- *_soc_min_constraint, *_soc_max_constraint. -->

### B-7 · A battery can't be more than full {#b-7}

<!-- *_capacity_constraint. Redundant (#143). -->

### B-8 · Net power is charging minus discharging {#b-8}

<!-- *_net_power_constraint. -->

## Power balance contribution

## Objective contribution

## Where to find each symbol in odys

<!-- Visible table: Symbol | Attribute | Type (Parameter, Variable, Result) | Unit -->

<!-- Bridge: Some batteries drive away. → [Electric vehicles and chargers](electric_vehicles.md) -->

---

Implemented in [`odys.optimization.formulations.storage`](../developer/api/optimization/formulations/storage.md), used by [`stationary_storage`](../developer/api/optimization/formulations/stationary_storage.md) and [`electric_vehicle`](../developer/api/optimization/formulations/electric_vehicle.md).
