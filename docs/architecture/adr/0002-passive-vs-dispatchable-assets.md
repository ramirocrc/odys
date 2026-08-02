# ADR 0002: Passive vs dispatchable assets

**Status:** accepted
**Date:** 2026-08-01
**Deciders:** maintainers (Phase 0 hygiene)

## Context

`FixedLoad` is a domain entity and portfolio member but is **not** in `AssetRegistry`.
Its profiles live on `Scenario` / `ScenarioParameters` and enter the power balance as
constants. Contributors must discover this by reading balance code.

Future profile-only assets (e.g. must-take renewables as non-dispatchable injection)
need a pattern.

## Decision

**Option A — Explicit passive asset kind (target).**

First-party assets will declare `kind=passive|dispatchable|coupling`. Passive assets
contribute parameters/scenario bindings and balance terms, but no decision variables.

**Phase 0 / near term:** `FixedLoad` stays as implemented (entity + scenario profiles +
balance constants). Migration to an explicit passive registry path is roadmap G15 (later).

## Consequences

### Positive

- Clear path for must-take / passive types when G15 lands
- FixedLoad is no longer an “accident” in the target model — it is the passive exemplar

### Negative

- Until G15, contributors still learn FixedLoad by reading balance code

## Alternatives considered

1. **Option B — Scenario data only:** smaller surface; weaker asset vocabulary
2. **Option C — Undocumented exception:** rejected
