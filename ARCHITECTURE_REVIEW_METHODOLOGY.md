# Architecture Review Methodology

How to review the odys data model: what each class means, how classes interact, and where the design gets in the way of change. This document defines the method. It contains no findings.

## 1. Purpose and non-goals

The review answers four questions:

1. Does every class have one clear meaning, and can a newcomer state it in one sentence?
2. Are the interfaces between classes and layers narrow, explicit and pointing in the right direction?
3. How much of the codebase must change to extend odys in the ways we expect?
4. Can the in-scope codebase be described by UML class and sequence diagrams that stay clear?

Non-goals: solver performance, model mathematics, test quality, and style already enforced by tooling (ruff, type checkers, complexipy, vulture). Those have their own guardrails (see `AGENTS.md`).

## 2. Ground rules

- **Scope:** `odys.domain`, `odys.parameters`, `odys.optimization` (including the model builder and registries), `odys.results`, `odys.energy_system`. User inputs such as `Scenario`/`StochasticScenario` and their string-keyed profiles are part of the data model under review, not fixed.
- **Baseline:** review `main` from scratch. The parked `target_architecture` branch is not an input, so it cannot anchor the analysis.
- **Public API:** odys is pre-1.0, so the review may recommend breaking changes to `odys/__init__.py` `__all__`. Every finding states its API impact so breaking changes are visible.
- **No code edits during the review.** Phases 1-4 produce documents only. Refactoring starts after the roadmap is approved.
- **Process:** phased, with a user checkpoint after each phase. Do not begin phase N+1 until the user approves the output of phase N.

## 3. The yardstick

### Stance on OOP and xarray

Objects own behaviour. xarray and linopy are implementation details that a class may hide, not structures that callers must know about. Where a class only carries data for others to compute on, or where callers reach into xarray internals to do a class's work, that is a finding. This does not mean forbidding vectorization. It means a class should offer an intention-revealing interface and vectorize behind it.

### Lens A: Single responsibility and cohesion

For each class ask:

- Can its purpose be stated in one sentence without "and"?
- Do all its fields and methods serve that purpose? Do groups of methods use disjoint groups of fields (a sign it is two classes)?
- Is it a data holder with logic living elsewhere (anemic), or logic with no clear owner (God object, "manager", "helper", "util")?
- Does its name match what it is? Are names consistent across layers (the same concept has the same name in `domain`, `parameters`, and `results`)?
- Does it distinguish entities, value objects, and services clearly?

### Lens B: Coupling and dependency direction

- Do dependencies point inward as documented in `AGENTS.md`, and are the import-linter contracts honest and sufficient?
- Is the interface a class exposes narrow? How many collaborators does it know about? Does any class touch the internals of another (Law of Demeter violations, attribute chains, private access)?
- Are there parallel structures that must be edited in lockstep (for example a registry, a store, and a builder branch for the same asset)? Those are hidden coupling.
- Are types from one layer leaking into another (xarray or linopy types in `domain` or the public API, apart from results)?
- Are there cycles, direct or through shared modules?

### Lens C: SOLID and composition over inheritance

- **Open/closed:** can a new asset, market or objective term be added without modifying existing classes? Where the code branches on asset type (`if params.<asset> is not None`), is that a justified simplicity or a missing abstraction?
- **Liskov:** where inheritance exists, can subclasses be used wherever the base is expected without special cases?
- **Interface segregation:** do callers depend on methods they do not use?
- **Dependency inversion:** do high-level policy classes depend on abstractions or on concrete details?
- **Composition over inheritance:** is each inheritance relationship "is-a" and used for polymorphism, or only for code reuse?
- Guard against over-abstraction: per `AGENTS.md`, a base class, protocol or registry needs at least two concrete users. A proposed abstraction with one user is a finding against the proposal.

### Describability check (UML)

The codebase should be describable with UML. Notation is Mermaid `classDiagram` and `sequenceDiagram`, which render in Markdown and live in git. Drawing the diagrams is part of the analysis, not only documentation of it. A class or flow that cannot be drawn cleanly is a finding, with the diagram as its evidence. Signs of trouble:

- A class with many collaborators, or whose diagram needs a long list of attributes to make sense.
- A sequence diagram with lifelines whose role is unclear, or with messages that pass through several intermediaries for no reason.
- Arrows pointing against the dependency direction, or the same collaboration appearing in several unrelated places.
- Two classes that look identical in the diagram but have different names (or the reverse).

## 4. Phases

### Phase 1: Inventory (checkpoint 1)

Produce a factual map, with no judgement yet:

- **Class catalogue** per layer: name, one-sentence meaning (as the code implies, not as we wish), key fields, collaborators, and whether it is public (`__all__`) or internal.
- **Class diagrams:** one UML `classDiagram` per layer showing inheritance, composition, association and "uses" links, plus one overview diagram. Optionally seed them with `pyreverse` (section 7) and correct by hand.
- **Sequence diagrams** for the main flows: `EnergySystem.optimize()` end to end, `build_parameters()`, model building (`EnergyAlgebraicModelBuilder`), and results extraction. Show real lifelines and messages, not intended ones.
- **Import graph** with the real dependency edges between subpackages (see section 7).
- **Flow trace:** how one asset (for example `Generator`) is represented at every stage from user input to result.

Output: `inventory.md`. The user confirms the map is accurate before analysis starts.

### Phase 2: Analysis (checkpoint 2)

- Apply lenses A, B and C to each class and layer boundary.
- **Change-impact traces** for the three stress scenarios below. For each, list every file that must change and count them. Compare against the ideal (files that should change) to quantify shotgun surgery.
  1. Add a new asset type (for example a heat pump).
  2. Add a new market, product or objective term (for example a reserve market).
  3. Add a second solver backend or modeling layer (anything beyond linopy and HiGHS).
- Record each issue using the finding template (section 5).

Output: `findings.md` plus the three traces. The user confirms, disputes or reclassifies findings.

### Phase 3: Target model (checkpoint 3)

- Propose a class model that resolves the accepted findings: each class's responsibility, public interface, collaborators, and dependency direction, as a Mermaid diagram plus a table.
- Include UML class diagrams of the target model and sequence diagrams of the same main flows as in Phase 1, so current and target can be compared side by side.
- Re-run the three stress scenarios against the proposal and show the reduced file count. Draw each scenario as a sequence diagram on the new design.
- Justify each new abstraction with at least two concrete users. Note alternatives considered and rejected.
- State every public API change.

Output: `target-model.md`.

### Phase 4: Roadmap (checkpoint 4)

- Break the move from current to target into ordered steps that can each be merged on its own with `just check` and `just test` green.
- Order by the prioritization matrix (section 6) and by dependency between steps.
- For each step: goal, files touched, tests that guard behaviour, API impact, and risk.
- Add a final item for keeping the diagrams as living documentation: where they live, whether they are generated or hand-written, and how drift from the code is detected. Decide this only after the target design is settled.

Output: `roadmap.md`. Approval here ends the review. Implementation is a separate task.

## 5. Finding template

```markdown
### F-<nn>: <short title>

- **Lens:** A (SRP/cohesion) | B (coupling) | C (SOLID/composition)
- **Location:** `path:line` (list all relevant places)
- **Evidence:** import-graph edge, change-impact trace, or code excerpt
- **Problem:** what is wrong, in one or two sentences
- **Impact:** blocks extension | causes bugs | hurts readability
- **Effort:** S | M | L
- **Proposed fix:** the direction, not a full design
- **API impact:** none | breaking (which exports)
```

Every finding must cite locations and evidence. A finding without a concrete `path:line` and evidence is an opinion and is dropped.

## 6. Prioritization

Rate each finding on impact and effort, then place it in the matrix.

| | Effort S | Effort M | Effort L |
| --- | --- | --- | --- |
| **Impact: blocks extension or causes bugs** | Phase 1: do first | Phase 2 | Phase 3 (plan carefully) |
| **Impact: hurts readability** | Phase 2 | Phase 3 | Backlog |

Impact definitions:

- **Blocks extension:** it appears in a stress-scenario trace as unnecessary changes, or prevents one of the scenarios.
- **Causes bugs:** it makes wrong states representable or requires lockstep edits that are easy to miss.
- **Hurts readability:** the class or interface is confusing, but the behaviour is safe.

Roadmap steps come from these phases, adjusted for dependencies between steps.

## 7. Evidence techniques

- **Enforced layering:** `uv run --locked lint-imports` (runs the `[tool.importlinter]` contracts in `pyproject.toml`). A passing run shows the declared contracts hold. It does not show the contracts are sufficient, so also inspect the real graph.
- **Real import graph:** `grep -rn "^from odys\|^import odys" src/odys` per subpackage, summarized as a matrix of package to package edges. Look for edges the contracts allow but the architecture does not intend, and for modules many others import (fan-in) or that import many others (fan-out).
- **Class inventory:** `grep -rn "^class " src/odys` for the catalogue, then read each class. Note base classes and decorators such as `@constraint`.
- **UML seeding:** `uvx --from pylint pyreverse -o mmd -p odys src/odys` can generate class diagrams without adding a project dependency. Verify the command works before relying on it (output format support varies by version), then correct the result by hand: it misses xarray-backed relationships and decorator-driven behaviour.
- **Mermaid conventions:** one diagram per layer and per flow, kept small enough to read. Class diagrams show only members that matter for responsibilities. Sequence diagrams name lifelines after real classes and messages after real methods. Mark public classes (those in `__all__`) in a note or stereotype.
- **Change-impact tracing:** follow the "Adding a new asset type" chain in `AGENTS.md` (entity, export, portfolio, validation, dimension, coordinates, parameters, variables, constraint group, builder branches, power balance, registry, results, tests, docs). For each stress scenario, walk the code to find every place a comparable existing feature (FlexibleLoad, a market, `CVaRTerm`, the HiGHS solver) appears. Search by its name and by `ModelDimension` members, and list every file.
- **Lockstep detection:** for a representative asset, search for its name across `src/` and note parallel per-asset structures (registries, stores, builder branches, results classes).

## 8. Where outputs live

Phase outputs live in `docs/architecture/` (`inventory.md`, `findings.md`, `target-model.md`, `roadmap.md`), so the Mermaid diagrams render in the zensical docs (`just docs`). Add each file to the "Architecture Review" section of the `nav` in `zensical.toml` when it is created. They are working documents until the roadmap is approved. Only this methodology file lives at the repo root.

## 9. Definition of done for the review

- Phase 1-4 outputs exist and each was approved at its checkpoint.
- Every finding uses the template and has evidence.
- Class diagrams cover all in-scope packages, and the main flows have sequence diagrams, for both the current and the target design.
- The three stress scenarios have before and after file counts.
- Every public API change is listed in one place.
- The roadmap steps are each independently mergeable and keep `just check` and `just test` green.
