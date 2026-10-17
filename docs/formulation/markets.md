---
icon: lucide/arrow-left-right
---

# Markets

<!-- Hook: How do I buy and sell? -->

<!-- Scope: added for every EnergyMarket. Each constraint: plain sentence, equation (logical then MILP form for binaries), read aloud, why it looks like this, good to know, facts line (Added · Binds · Name). -->

## Sets and indices

## Variables

<!-- p^buy, p^sell ≥ 0; y^trade ∈ {0, 1}. -->

## Constraints

### M-1 · Trades stay within the volume limit {#m-1}

<!-- market_max_{sell,buy}_volume_constraint. Redundant (#144). -->

### M-2 · A market buys or sells, not both {#m-2}

<!-- market_mutual_exclusivity_{sell,buy}_constraint, big-M = max_trading_volume_per_step. Payoff-equivalent (#140). -->

### M-3 · Some markets only go one way {#m-3}

<!-- market_buy_only_constraint, market_sell_only_constraint. -->

### Stage-fixed markets

<!-- Link to NA-1 on Scenario structure. -->

## Power balance contribution

## Objective contribution

## Where to find each symbol in odys

<!-- Visible table: Symbol | Attribute | Type (Parameter, Variable, Result) | Unit -->

<!-- Bridge: Buying isn't the only option: you can make your own power. → [Generators](generators.md) -->

---

Implemented in [`odys.optimization.formulations.energy_market`](../developer/api/optimization/formulations/energy_market.md).
