# Architecture roadmap

**Date:** 2026-08-02
**Inputs:** [as-is-scorecard.md](as-is-scorecard.md), [target-architecture.md](target-architecture.md)
**Nature:** recommendations — not a committed delivery plan until explicitly scheduled
**Status:** Phases 0–3 + **G11a + G12** done. **No runtime user/plugin assets** (G13/G11b rejected). Next optional: G10 / Phase 4.

## Product stance

Odys supports **first-party assets only** via `AssetRegistry` and the public domain API.
Users cannot inject custom asset types at runtime. New asset types are maintainer work
(registry + production stack).

## 1. Gap matrix

Impact / effort: S ≈ hours–day, M ≈ days–week, L ≈ multi-week.

| ID | Gap | Impact | Effort | Horizon | Notes |
|----|-----|--------|--------|---------|-------|
| G1 | Domain → optimization inversion (`portfolio` → `AssetRegistry`) | High | S | **Done (Phase 0)** | Removed `assets_by_type` |
| G2 | CI AST contracts for layer rules | High | S | **Done (Phase 0)** | `architecture_metrics.py --check` in `just check` |
| G3 | ADR pack for markets / FixedLoad / contributions / results API | Med | S | **Done (Phase 0)** | ADRs 0001–0004 accepted |
| G4 | Export results in `__all__`; rename to `OptimalDispatchResults` | Med | S | **Done (Phase 0)** | Hard rename, no alias |
| G5 | Fix misleading `domain` purity docstring | Low | S | **Done (Phase 0)** | Documents enforced dependency rule |
| G6 | Registry owns constraint group factory + param field binding | High | M | **Done (Phase 1)** | Builder-only; param *production* in G11a |
| G7 | Asset contribution ports for power balance + profit | High | L | **Done (Phase 2)** | Registry assets only; FixedLoad residual; Charger no-op |
| G8 | Results depend on solution schema only | Med | M | **Done (Phase 3)** | `SolutionSchema`; forbid `results → optimization` |
| G9 | Deduplicate `*Dispatch` (generic + thin wrappers) | Med | M | **Done (Phase 3)** | `_DispatchBase` + thin public wrappers |
| G10 | Split `validation.py` into composable modules | Med | M | **Later** | Understandability; already pure |
| G11 | Param factories (first-party assembly) | Med | M | **Done (G11a)** | Context + `.build`; closed ESP bag |
| G12 | MILP property god-object → typed `ModelVariables` view | Med | M | **Done** | `model.vars.*`; field name = linopy name |
| G13 | Runtime plugin inject (`extra_specs`) | — | — | **Rejected** | First-party only; complexity not wanted |
| G14 | Markets ownership cleanup | Med | M | **Later** | After ADR 0001 |
| G15 | Passive asset first-class path for FixedLoad | Med | M | **Later** | After ADR 0002 |

## 2. Strategic options

### Option A — Do nothing further

- **When:** asset surface is frozen; shipping features only
- **Cost:** new first-party assets still touch params class + ESP field + validation/MILP accessors (~5–7)
- **Risk:** MILP accessors grow with each asset
- Note: Phases 0–3 and G11a are done; plugin injection is out of scope.

### Option B — Boundary hygiene only — **DONE (Phase 0)**

G1–G5 shipped.

### Option C — First-party registry spine — **DONE (Phases 0–3 + G11a)**

| Slice | Status |
|-------|--------|
| G6 registry builder | **Done** |
| G7 contribution ports (registry only) | **Done** |
| G8–G9 results schema + generic dispatch | **Done** |
| G11a param factories | **Done** |
| G12 typed `model.vars` | **Done** |
| Runtime plugins (G13/G11b) | **Rejected** |

### Option D — Big-bang package restructure

- **Not recommended** while G12 remains higher ROI if needed

## 3. Phased plan

### Phase 0 — Stabilize — **DONE**

Domain pure, layer CI, ADRs, results public rename.

### Phase 1 — Registry completion — **DONE**

Builder iterates registry for vars/constraints; `parameters_attr` + `constraint_group`.

### Phase 1b — Parameter factories (G11a) — **DONE**

`ParamBuildContext`, `*Parameters.build(ctx)`, `build_energy_system_parameters`, thin `EnergySystem.build_parameters`. Closed bag only.

### Phase 2 — Contribution ports (G7) — **DONE**

Registry contribution ports for balance/profit. Kernel loops **`AssetRegistry` only**. FixedLoad residual; Charger no-op. Constraint modules use `TYPE_CHECKING` for `EnergyMILPModel`.

### Phase 3 — Results & boilerplate — **DONE**

`SolutionSchema`, `_DispatchBase`, results leaf.

### Phase 3b — Typed variable view (G12) — **DONE**

`ModelVariables` with explicit annotations; `EnergyMILPModel.vars`; construction from `ModelVariable` + linopy names; typed field names equal linopy names (no accessor indirection); contract test field ↔ name parity.

### Phase 4 — Language cleanup (as needed)

G14 markets, G15 FixedLoad, package moves only if navigation improves.

## 4. CI guardrails

```text
forbidden:
  odys.domain.*          -> odys.optimization.* | odys.results.* | odys.solvers.* | odys.energy_system
  odys.results.*         -> odys.optimization.*
  odys.optimization.constraints.* -> odys.results.*
```

## 5. KPI dashboard

| KPI | After Phases 0–3 + G11a |
|-----|-------------------------|
| Domain → outer leaks | **0** |
| Kernel equation edits / new first-party dispatchable | **0** (registry ports) |
| Param assembly switchboard | **gone** |
| Runtime user asset injection | **not supported** |
| Production asset edit sites | **~5–7** |
| Results → optimization | **none** |
| Layer check in CI | **yes** (results↛opt) |

## 6. Recommended decision

1. ~~Phases 0–3 + G11a~~ — **done.**
2. ~~Runtime plugins~~ — **rejected** (product decision).
3. ~~**G12**~~ — **done** (`model.vars`).
4. **Defer** G10/G14/G15 until a concrete need.
