# Odys architecture (internal)

**Status:** internal review pack — Phases 0–3 + G11a done; first-party assets only — **not** linked in site nav.

This folder holds the architecture scorecard, target design, roadmap, and ADRs from
the dual-track review. Complete: hygiene, registry builder, contribution ports (registry
only), results schema + dispatch, G11a param factories, G12 typed `model.vars`.
**No runtime user asset plugins.** Optional next: G10, Phase 4 — see [roadmap.md](roadmap.md).

Promote individual pages into the public docs site only after they are polished and
explicitly added to `zensical.toml` nav.

| Document | Purpose |
|----------|---------|
| [charter.md](charter.md) | Review goals, quality axes, non-goals |
| [as-is-scorecard.md](as-is-scorecard.md) | Current structure, coupling, hotspots, scores |
| [target-architecture.md](target-architecture.md) | Ideal architecture independent of today's tree |
| [roadmap.md](roadmap.md) | Gap matrix and phased recommendations |
| [adr/](adr/) | Architecture Decision Records |

## Regenerating metrics

```bash
just architecture-metrics
# or
uv run python scripts/architecture_metrics.py
uv run python scripts/architecture_metrics.py --check   # CI mode (also in just check)
```
