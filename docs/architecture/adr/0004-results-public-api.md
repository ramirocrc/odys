# ADR 0004: Results public API and type naming

**Status:** accepted
**Date:** 2026-08-01
**Deciders:** maintainers (Phase 0 hygiene)

## Context

`EnergySystem.optimize()` returns results objects that examples and docs import deeply.
The type was historically misspelled (`OptimalDisptachResults`) and was not in
`odys.__all__`, despite being the primary library output.

Historically, results imported optimization symbols (`ModelDimension`, `ModelVariable`,
`EnergySystemParameters`), coupling the public output type to internal model schema.

## Decision

1. **Public export:** `OptimalDispatchResults` is part of the stable top-level API
   (`from odys import OptimalDispatchResults` and `odys.results`).
2. **Naming:** hard rename to `OptimalDispatchResults` (correct spelling). **No**
   compatibility alias for `OptimalDisptachResults` (library still alpha).
3. **Coupling:** solution-schema boundary (Phase 3 / G8) — results depend only on
   `SolutionSchema` (+ domain exceptions); CI forbids `results → optimization`.
   G9: generic `_DispatchBase` + thin public wrappers.

## Consequences

### Positive

- Public API matches the real user journey (configure → optimize → results)
- Correct spelling before a wider audience freezes the typo
- Results package is a leaf (`I ≈ 0.20`); no optimization imports

### Negative

- Breaking rename for any external code still using the old name
- Dim/var name strings live in `results/schema.py` (optional contract test vs
  `ModelVariable` if drift becomes a pain)

## Alternatives considered

1. Export only, keep typo — rejected
2. Rename + deprecated alias — unnecessary while alpha
3. Full schema decoupling in the same change — done later as G8/G9 (Phase 3)
