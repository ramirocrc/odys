# ADR 0003: System contribution ports

**Status:** accepted
**Date:** 2026-08-01
**Deciders:** maintainers (Phase 0 hygiene)

## Context

Power balance (`ScenarioConstraints`) and per-scenario economics
(`EnergyMILPModel.per_scenario_profit`) hardcode every asset type. They are the main
reason a new first-party asset requires edits outside its own module.

**As of Phase 2 (G7):** system equations (balance + profit) are contribution-port
driven for **registered** assets. Variable creation and asset constraint wiring were
already registry-driven in Phase 1 (G6). FixedLoad remains a kernel residual until G15.

## Decision

**Option A — Contribution ports on `AssetRegistry` members (implemented).**

Each registered asset exposes (via `AssetSpec`):

- `power_balance_terms(model_view, params) -> terms`
- `profit_terms(model_view, params) -> terms`

Kernel sums contributions over **`AssetRegistry` only**. Assets own broadcasting and signs.

**Out of scope:** runtime user/plugin asset injection. Odys is first-party assets only;
new types require a registry entry and production stack (maintainer change).

### Implementation notes

- **Contract:** contributors on `AssetSpec` —
  `(EnergyMILPModel, EnergySystemParameters) -> LinearExpression | None`.
  Balance dims `(scenario, time)`; profit dims `(scenario,)`. `+` = injection / revenue.
- **Kernel collectors:** `optimization/model/contributions/collect.py` iterate `AssetRegistry`.
- **Migrated:** Generator, StandaloneStorage, Market, FlexibleLoad, ElectricVehicle.
- **Charger:** no balance/profit ports (coupling only).
- **FixedLoad:** kernel residual in power balance until G15.

## Consequences

### Positive

- Lower extension cost for new **first-party** assets: no edits to balance/profit kernel loops
- Clear product boundary: supported assets = registry

### Negative

- linopy expression composition still needs care per asset
- AST metrics count `TYPE_CHECKING` edges into a multi-node SCC (runtime remains acyclic)
- Adding an asset still requires maintainer multi-file work (params, validation, etc.)

## Alternatives considered

1. **Option B — Data-driven table of var coefficients:** simpler but weak for EV/charger
2. **Option C — Status quo forever:** rejected for registry spine
3. **Runtime plugin inject (`extra_specs`):** rejected — unnecessary complexity; users shall not define custom assets
