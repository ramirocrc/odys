---
icon: lucide/scale
---

# Power balance

<!-- Hook: What ties every asset together? -->

<!-- Scope: the single constraint that ties every asset and market together, and the fixed loads (D^fix), which appear only here. -->

## Fixed loads

<!-- D^fix_{l,s,t} from the LoadProfile; a constant demand with no variables and no objective term. -->

## PB-1 · Supply meets demand at every step {#pb-1}

<!-- Σ injections = 0 ∀ s, t: generators + battery discharge − charge + market buy − sell − fixed demand − flexible demand. Hard equality, no slack, single bus. Chargers inject nothing. Model name: power_balance_constraint. -->

## Where to find each symbol in odys

<!-- Visible table: Symbol | Attribute | Type (Parameter, Variable, Result) | Unit -->

<!-- Bridge: Who fills the gap? First, the outside world. → [Markets](markets.md) -->

---

Implemented in [`odys.optimization.power_balance`](../developer/api/optimization/power_balance.md) and [`odys.optimization.formulations.fixed_load`](../developer/api/optimization/formulations/fixed_load.md).
