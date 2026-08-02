# Architecture review charter

**Date:** 2026-08-02
**Mode:** full scorecard (evolvability, understandability, correctness boundaries, coupling)
**Scope:** review pack through Phase 3 + G11a (first-party registry spine). Further optional
work follows [roadmap.md](roadmap.md) (G10, G12, G14–G15, Option D).

## Product context

Odys is a Python library for stochastic multi-asset energy portfolio optimization.
The user journey is:

```
Assets → AssetPortfolio → Scenario(s) → EnergySystem → optimize() → Results
```

Stochastic optimization is the default; a single deterministic `Scenario` is
normalized to one `StochasticScenario` with probability 1.

**Asset surface:** first-party types only (`AssetRegistry` + public domain API). Users
do not register or inject custom asset types at runtime.

## Primary use cases (review drivers)

1. Configure multi-asset portfolio + markets + scenarios → optimize → inspect dispatch
2. (Maintainer) Add a new first-party asset type with decision variables
3. Add or compose objective terms (e.g. CVaR-like risk)
4. Swap solver backends (HiGHS / Gurobi / CPLEX / SCIP)

## Quality axes (score 1–5)

| Axis | Question |
|------|----------|
| **Layer purity** | Do dependencies point inward? Can domain be reasoned about without linopy? |
| **Extension cost** | How many files must change to add a **first-party** asset? |
| **Cohesion vs size** | Are large modules coherent, or god-objects / dump sites? |
| **Public API stability** | Is the exported surface intentional and complete vs de-facto public? |
| **Testability** | Can layers be unit-tested without solvers / full pipeline? |
| **Cognitive load** | How many special cases must a contributor hold in their head? |

## Non-goals (until explicitly scheduled)

- Runtime user/plugin asset injection
- Validation module split (G10)
- Markets ownership / FixedLoad passive path (G14–G15)
- Changing MILP formulation or numerical correctness audits
- Adding new asset types or product features (unless separately requested)
- Big-bang package restructure (Option D)

## Already delivered

- Domain purity, layer CI, ADRs 0001–0004 (Phase 0)
- Registry builder vars/constraints (Phase 1 / G6)
- Contribution ports over `AssetRegistry` (Phase 2 / G7)
- Results schema leaf + dispatch base (Phase 3 / G8 + G9)
- Param factories + `ParamBuildContext` (G11a)
- Typed `ModelVariables` / `model.vars` (G12)

## Method

**Dual-track:** as-is metrics + greenfield ideal → gap matrix, roadmap, ADRs.

## Artifacts

| Artifact | Path |
|----------|------|
| As-is scorecard | `docs/architecture/as-is-scorecard.md` |
| Target architecture | `docs/architecture/target-architecture.md` |
| Roadmap | `docs/architecture/roadmap.md` |
| ADRs | `docs/architecture/adr/` |
| Metrics script | `scripts/architecture_metrics.py` |
