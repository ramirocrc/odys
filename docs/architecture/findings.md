---
icon: lucide/search-check
---

# Phase 2: Findings

Analysis of the odys data model on `main` (`edf58ca`), following `ARCHITECTURE_REVIEW_METHODOLOGY.md`. It builds on the [Phase 1 inventory](inventory.md) and the checkpoint 1 decisions recorded there (section 8).

Each finding uses the template from the methodology. Lenses: **A**: single responsibility and cohesion; **B**: coupling and dependency direction; **C**: SOLID and composition over inheritance; **D**: describability (UML). All line numbers refer to `main`.

This document diagnoses problems. It proposes only the *direction* of each fix; the design is Phase 3.

---

## 1. Summary

The data model has good local pieces: frozen pydantic entities, a clear domain/parameters/optimization/results pipeline, a working `@constraint` discovery mechanism, and strongly typed variables. The structural problem is one pattern that repeats across the codebase:

> **An asset type is not a class. It is a name repeated in about 15 places.**

"Generator", "StandaloneStorage", "Market" and so on each exist as a domain entity, and then again as a portfolio property, a scenario field, validation functions, a coordinates field, a dimension, a parameters class, a parameters-bag field, variable declarations, typed-variable attributes, builder branches, a constraint group, a power-balance branch, a profit branch, a results property, a dispatch class, and a registry entry. No object owns the full behaviour of an asset. Most findings below (F-01 to F-09) are facets of this pattern.

Adding the EV fleet feature (PR #98) touched **93 files: 29 in `src/`, 24 tests, 34 docs**. The traces in section 2 predict **18 `src/` files** for the next asset type. A design where each asset owns its behaviour would need about 3.

| Impact / effort | S | M | L |
| --- | --- | --- | --- |
| **Blocks extension or causes bugs** | F-10, F-19, F-20 | F-03, F-05, F-06, F-07, F-11, F-15 | F-01, F-08, F-09, F-12 |
| **Hurts readability** | F-02, F-13, F-18 | F-04, F-14, F-16, F-17 | none |

Section 6 turns this matrix into roadmap phases. Section 7 lists five bugs found along the way; they are out of scope for the review but should be fixed.

---

## 2. Change-impact traces

Method: for each stress scenario, find every place a comparable existing feature appears in `src/` (by name, `ModelDimension` member, and call sites), and list the files that must change. "Ideal" is the count if the concept were owned by one class plus its registration.

### T1: Add a new asset type (e.g. a heat pump: a controllable electrical consumer with its own variables, a cost, and results)

| # | File | Change | Lockstep with |
| --- | --- | --- | --- |
| 1 | `domain/entities/heat_pump.py` | new entity | none |
| 2 | `odys/__init__.py` | export | none |
| 3 | `domain/entities/portfolio.py` | new `heat_pumps` property | isinstance filter per type |
| 4 | `domain/scenarios.py` | new profile field, if it has exogenous data | `Scenario` has one field per asset kind |
| 5 | `domain/validation.py` | profile consistency; power/energy sufficiency must learn the new supply or demand | 16 functions that enumerate asset kinds |
| 6 | `optimization/model/dimensions.py` | new `ModelDimension` member | none |
| 7 | `optimization/model/coordinates.py` | new `CoordinatesStore` field and `get_coordinates` mapping entry | `ModelDimension` |
| 8 | `energy_system.py` | coordinates block and parameters block in `build_parameters` | 2 branches |
| 9 | `parameters/entity_parameters/heat_pump_parameters.py` | new parameters class | entity fields |
| 10 | `parameters/energy_system_parameters.py` | new optional field | none |
| 11 | `optimization/model/variable_definitions.py` | registry entries and `HEAT_PUMP_VARIABLES` group | `VariableStore` |
| 12 | `optimization/model/milp_model.py` | `VariableStore` attributes; `per_scenario_profit` branch | registry |
| 13 | `optimization/model/model_builder.py` | variable branch and constraint-group branch | 2 branches |
| 14 | `optimization/constraints/heat_pump_constraints.py` | new `ConstraintGroup` | none |
| 15 | `optimization/constraints/scenario_constraints.py` | power-balance branch | none |
| 16 | `optimization/model/registry.py` | `AssetRegistry` entry (unused; see F-02) | none |
| 17 | `results/dispatch.py` | new `HeatPumpDispatch` (~75 lines) | 6 sibling classes |
| 18 | `results/optimization_results.py` | property, `_has_*` flag, `__slots__` entry | none |
| (19) | `pyproject.toml` | import-linter independence contract (branch only) | none |

**Before: 18 `src/` files** (3 new, 15 modified), plus ~6 test files, ~5 docs pages, and `CHANGELOG.md`. **Ideal: 3** (entity, its model component, and the export). Missing any lockstep site other than 1, 9 and 14 does not fail at import time. It fails later (a variable is not added, the balance ignores the asset, or results raise), or it silently does nothing (validation, sections 3 and 5).

Empirical check: PR #98 (EV + Charger) touched 29 `src/` files, a count inflated by the storage rename done in the same PR.

### T2a: Add a new market product (e.g. a reserve or capacity market)

A reserve product differs from `EnergyMarket`: it trades capacity, has its own prices, and couples to assets through headroom (a generator cannot sell reserve it is already using).

Files: `domain/entities/market.py` (a new product type or a field on `EnergyMarket`), `__init__.py`, `energy_system.py` (the `markets` union type, `collection_of_markets`, coordinates, parameters), `domain/scenarios.py` (new price field), `domain/validation.py` (price consistency), `dimensions.py` and `coordinates.py` (new dimension or reuse of `market`), `market_parameters.py` or a new class, `energy_system_parameters.py`, `variable_definitions.py`, `milp_model.py` (`VariableStore` plus profit), `model_builder.py`, `market_constraints.py` or a new group, and **every asset group that can offer reserve** (`generator_constraints.py`, `standalone_storage_constraints.py`, `electric_vehicle_constraints.py`) for headroom, `results/dispatch.py`, `optimization_results.py`.

**Before: ~18 `src/` files.** **Ideal: 3-4** (product entity, its model component, one "headroom" capability that each capable asset component implements, and the export). The cross-asset coupling is the hard part. Today there is no place for "an asset that can offer upward flexibility" to declare that capability once.

### T2b: Add a new objective term (e.g. a peak-demand charge or an emissions penalty)

Files: `domain/objective.py` (new term class and **a new field on `Objective`**, since the terms are fixed attributes), `__init__.py`, `optimization/model/objectives.py` (new branch in `build_objective`), `variable_definitions.py` (auxiliary variables plus a group), `milp_model.py` (`VariableStore`), `model_builder.py` (variable branch and group branch, as for CVaR), a new constraints group, and `per_scenario_profit` if the term depends on assets.

**Before: 7-8 `src/` files.** **Ideal: 2** (term class, and its contribution to the model).

### T3: Add a second solver backend, or a second modeling layer

- **A new solver inside linopy** (e.g. COPT or Xpress) needs `SolverName` and one translator class plus its dict entry: **2 files**. This extension point works (`SolverOptionTranslator` has 4 implementations).
- **A different modeling layer** (e.g. pyoptinterface or Pyomo): **17 of the modules** in `optimization/`, `solvers/` and `results/` reference linopy types or linopy/xarray algebra (`.shift`, `.where`, `.rolling`, `.sel` on variables). Every constraint expression is written directly in linopy, so this is a rewrite of the optimization layer. **Ideal: depends on whether we want this at all** (see F-12).

---

## 3. Describability check

Results of drawing the Phase 1 diagrams:

| Diagram | Problem found while drawing | Finding |
| --- | --- | --- |
| No sequence diagram | **There is no lifeline for "a generator"**. Its behaviour is spread over `validation.py`, `GeneratorParameters`, `GeneratorConstraints`, `EnergyMILPModel.per_scenario_profit`, `ScenarioConstraints` and `GeneratorDispatch`, so no diagram can ask it to do anything. | F-01, F-03 |
| Class 3.2 (domain) | `Scenario ..> EnergyEntity : keyed by name (string)`: the relationship is a string lookup, which UML cannot express as an association. `EnergyMarket` inherits `EnergyEntity` but has no aggregation from `AssetPortfolio`, so it floats. | F-09, F-10 |
| Class 3.4 (model) | `AssetRegistry` has no incoming edge (unused). `VariableStore` needs a note ("set via `setattr`, may be missing"), so its declared attributes are not its real ones. | F-02, F-07 |
| Class 3.5 (constraints) | 8 subclasses all point at `EnergyMILPModel` but actually use two things behind it (`vars`, `parameters.<asset>`), which the diagram hides. | F-06 |
| Sequence 4.2 (`optimize`) | The solver lifeline **creates** the results object and passes `parameters` into it, which is an arrow from solving to result shaping. | F-13 |
| Sequence 4.4 (build) | The `ConstraintGroup` lifeline talks to three objects (`M.parameters`, `M.vars`, `L`) to add one constraint. The builder repeats the same "if asset present" decision twice. | F-05, F-06 |
| Overview 3.1 | `EnergySystem` has dependency arrows to every layer. `EnergySystemParameters` is aggregated by both `EnergyMILPModel` and `OptimalDisptachResults`. | F-04, F-13, F-16 |
| Class 3.3 + 3.6 | `Storage` is one box in the domain but two unrelated boxes in parameters, constraints and results. | F-08 |

---

## 4. Findings

### F-01: No asset abstraction owns an asset's behaviour; each asset type is spread over ~15 lockstep sites

- **Lens:** B (hidden coupling), C (open/closed)
- **Location:** `portfolio.py:95-163`, `scenarios.py:35-50`, `validation.py` (whole module), `coordinates.py:36-60`, `dimensions.py:6`, `energy_system.py:127-181`, `energy_system_parameters.py:36-41`, `variable_definitions.py:39-217`, `milp_model.py:26-46`, `:100-159`, `model_builder.py:83-144`, `scenario_constraints.py:19-53`, `optimization_results.py:27-174`, `dispatch.py`, `registry.py:52`
- **Evidence:** trace T1 (18 files before, 3 ideal); PR #98 touched 29 `src/` files; describability: no asset lifeline exists; "generator" appears in 18 files across 6 packages (inventory section 6).
- **Problem:** The code branches on asset type by hand in every layer (`if params.generators is not None`, one property or field per type) instead of iterating over polymorphic objects. Adding or changing an asset means finding every branch; missed branches fail late or silently.
- **Impact:** blocks extension
- **Effort:** L
- **Proposed fix:** Introduce one model-side class per asset type (working name: *asset component*) that owns, for that asset: coordinates, vectorized parameters, variables, constraints, contributions to power balance and profit, and result extraction. The builder, power balance, objective and results then iterate over a collection of components. Domain entities stay free of xarray and linopy, and each maps to its component. This has six concrete users today, so it passes the "two users" rule.
- **API impact:** none for inputs. `results.<asset>` accessors may change shape (see F-14).

### F-02: `AssetRegistry` is an unused, partial copy of the asset concept

- **Lens:** A, B
- **Location:** `optimization/model/registry.py:35-100`
- **Evidence:** no callers in `src/`, tests, or examples (inventory 2.4); `AGENTS.md` still asks contributors to keep it in sync.
- **Problem:** It records entity class, parameters class, dimension and variables per asset, but not constraints, balance, profit or results, and nothing reads it. It is maintenance cost with no behaviour, and it gives the false impression that a registry drives the model.
- **Impact:** hurts readability
- **Effort:** S
- **Proposed fix:** Remove it, or absorb it into F-01's components. Drop the `AGENTS.md` instruction.
- **API impact:** none

### F-03: Domain entities are anemic; their invariants and capabilities live in a 608-line procedural module

- **Lens:** A
- **Location:** `validation.py:21-608`; `electric_vehicle.py:29-76` (validation methods invoked externally from `validation.py:563-583`); `validation.py:370-397` (`_max_available_power_profile` enumerates generators, standalone storages and markets)
- **Evidence:** `validation.py` imports 6 entity classes and has 16 functions, most of which are per-asset-kind. `ElectricVehicle.validate_no_overlapping_trips()` is a single-entity invariant, yet it runs only when `EnergySystem` is built, not when the EV is created. The power-sufficiency check does not include EV discharge. That is a direct consequence of each check having to know every asset kind, and every new asset type must be added by hand.
- **Problem:** Entities are data holders. Knowledge such as "what power can this asset supply at most" or "is this asset's own data consistent" is written outside the asset, once per asset kind. This makes validation another lockstep site (F-01) and allows invalid entities to exist until system construction.
- **Impact:** blocks extension (and is a latent source of wrong validations)
- **Effort:** M
- **Proposed fix:** Move single-entity invariants into entity validators (EV trip overlap, `min_soc_at_departure` versus `soc_start`). Give entities small polymorphic queries used by cross-entity checks (for example "maximum supply power" and "minimum demand"), so `validation.py` reduces to system-level rules that iterate over entities. Cross-entity checks that need the horizon stay at system level.
- **API impact:** some errors are raised earlier (at entity creation instead of `EnergySystem` creation). Behaviour-compatible otherwise.

### F-04: `EnergySystem` is both the problem definition and the workflow orchestrator

- **Lens:** A, B
- **Location:** `energy_system.py:39-200`
- **Evidence:** fan-out 19, the highest in the codebase (inventory 5); imports from every layer, including 7 parameters classes; `build_parameters()` contains a second copy of the asset-type branching (`:136-181`). Overview diagram: dependency arrows to every package.
- **Problem:** One class is (a) the validated description of the problem (portfolio, horizon, scenarios, markets, objective), (b) the assembler of coordinates and parameters, and (c) the pipeline that builds, solves and returns results. Its "one sentence" needs two "and"s.
- **Impact:** hurts readability (and contributes to F-01's lockstep via `build_parameters`)
- **Effort:** M
- **Proposed fix:** Keep `EnergySystem` as the validated problem definition with a thin `optimize()` façade. Move parameter assembly to the model side (the F-01 components build their own coordinates and parameters), and move the build → solve → results pipeline into one dedicated object in the composition root.
- **API impact:** `optimize()` can remain. `build_parameters()` becomes internal or disappears.

### F-05: `EnergyMILPModel` is a god object

- **Lens:** A
- **Location:** `milp_model.py:59-159`
- **Evidence:** it holds the linopy model, the parameters, the typed variables, and `per_scenario_profit()` with one branch per asset type (60 lines). Fan-in 11. Sequence 4.4: every constraint group reaches through it.
- **Problem:** "The algebraic model" and "what each asset contributes to profit" are different responsibilities. Profit rules for generators, markets, storage, EVs and flexible loads all change this class.
- **Impact:** blocks extension (T1, T2a, T2b all modify it)
- **Effort:** M
- **Proposed fix:** Reduce it to the algebraic model plus variable access. Each asset component contributes its own profit and power-balance terms, which are summed generically.
- **API impact:** none

### F-06: Constraint groups depend on the whole model and navigate its internals

- **Lens:** B (Law of Demeter, interface segregation)
- **Location:** `generator_constraints.py:19-31`, `standalone_storage_constraints.py:31-39`, `electric_vehicle_constraints.py:31-39`, `charger_constraints.py:24-36`, `market_constraints.py:19-26`, `flexible_load_constraints.py:18-25`, `scenario_constraints.py:14-17`
- **Evidence:** every group takes `EnergyMILPModel` and uses `self.model.vars.<x>` and `milp_model.parameters.<asset>`. Seven constructors re-check for `None` and raise `ValueError` (not an `Odys*` error, contrary to `AGENTS.md`). `ScenarioConstraints` sets `self.model` but reads `self.model.linopy_model.variables[...]` directly (`:82`). Sequence 4.4: three hops per constraint.
- **Problem:** A group needs its own parameters and variables but receives everything. The `None` checks exist only because the dependency is too broad. The builder already knows the block is present.
- **Impact:** blocks extension (each group is coupled to the shape of `EnergyMILPModel` and `EnergySystemParameters`)
- **Effort:** M
- **Proposed fix:** Inject exactly the group's inputs (typed parameters and typed variables) so absence is impossible by construction. Under F-01, constraints become methods of the asset component.
- **API impact:** none

### F-07: Each decision variable is declared three times, and the typed view can lie

- **Lens:** B, C
- **Location:** `variable_definitions.py:36-217`, `milp_model.py:19-56`
- **Evidence:** a variable exists as (1) a `VariableDefinitionRegistry` member, (2) a `VariableStore` annotation, and (3) group membership computed by dimension filtering with a hand-written exception (`EV_VARIABLES` excludes `CHARGER_EV_ASSIGNMENT`, `:210-216`). `VariableStore` annotates all 21 attributes but sets only the ones present, with `setattr` (`:55-56`). A missing variable passes the type checkers and raises `AttributeError` at runtime.
- **Problem:** Three declarations must stay in sync, and the type checker cannot help, because the annotations are not backed by construction.
- **Impact:** causes bugs (type-checked code can fail at runtime) and blocks extension
- **Effort:** M
- **Proposed fix:** Each asset component declares and owns its variables as a small typed object (for example "generator variables" with `power`, `status`, `startup`, `shutdown`), created together with the component so that presence is guaranteed.
- **API impact:** none

### F-08: Storage is modelled by inheritance in the domain but duplicated everywhere else; an EV "is a" storage

- **Lens:** C (composition over inheritance), A
- **Location:** `storage.py:16`, `electric_vehicle.py:12`; `standalone_storage_parameters.py` and `electric_vehicle_parameters.py:42-58` (same 11 fields twice); `standalone_storage_constraints.py` and `electric_vehicle_constraints.py` (the same 9 constraints, delegated to `storage_constraints.py`); `dispatch.py:100-251` (two near-identical dispatch classes)
- **Evidence:** class diagrams 3.3 and 3.6 show one box in the domain and two in each other layer. Checkpoint 1 defined `ElectricVehicle` as "an electric vehicle", not "a storage". `Storage.asset_type()` is abstract but has no callers.
- **Problem:** Inheritance is used for code reuse of battery fields, not for polymorphism: no code handles `Storage` generically. The reuse then stops at the domain layer, so battery physics is duplicated in three other layers. An EV is a vehicle that *has* a battery.
- **Impact:** blocks extension (any battery change is made 3-4 times; a third battery-bearing asset would triple it)
- **Effort:** L
- **Proposed fix:** Introduce a battery value object (capacity, powers, efficiencies, SOC limits, degradation, self-discharge) composed into `StandaloneStorage` and `ElectricVehicle`. On the model side, one battery component (parameters, variables, constraints, dispatch), parameterised by its dimension, is reused by both assets. Remove `Storage.asset_type()`.
- **API impact:** breaking. Constructors change shape (for example `ElectricVehicle(name, battery=Battery(...), trips=...)`). Allowed pre-1.0.

### F-09: `Scenario` is a per-asset-kind bag of string-keyed profiles

- **Lens:** A, B; illegal states representable
- **Location:** `scenarios.py:17-68`; `validation.py:64-255` (three consistency functions with the same shape; the working branch already factors them); `scenario_parameters.py:13-146`
- **Evidence:** trace T1 row 4 and T2a (every exogenous series is a new `Scenario` field, a new validation function and a new `ScenarioParameters` property). The domain class diagram cannot draw the scenario-to-asset relationship except as "keyed by name (string)". A typo in a key is caught only by `EnergySystem` validation, not by `Scenario`. `ScenarioParameters` fills missing generator profiles with `inf` (`:127`), which silently means "no limit".
- **Problem:** `Scenario` knows every asset kind that has time series, so it grows with every such asset. References to assets are strings, so the type system cannot connect a profile to its asset or check its meaning (capacity versus load versus price).
- **Impact:** blocks extension
- **Effort:** L
- **Proposed fix:** Make scenario data generic over assets. For example, a scenario holds typed profile objects that each name their asset and kind, or each asset type declares the time series it needs and `Scenario` maps asset to data. Validation of "every asset has its required series" becomes one generic rule. Phase 3 picks the design. Checkpoint 1 confirmed `Scenario` is in scope.
- **API impact:** breaking (scenario construction)

### F-10: `EnergyMarket` is an `EnergyEntity` but not a portfolio member; a market placed in the portfolio is silently ignored

- **Lens:** C (substitutability), A; illegal state representable
- **Location:** `market.py:23`, `portfolio.py:32-55` (accepts any `EnergyEntity`), `energy_system.py:77`, `:118-125`
- **Evidence:** `AssetPortfolio([gen, market])` is accepted. No accessor returns markets and no validation rejects them, so the market does not enter the model. Domain diagram: `EnergyMarket` has no association to anything that uses it.
- **Problem:** The base class says "a market is the same kind of thing as an asset", but the system treats it as a different kind. The portfolio's type (`EnergyEntity`) is wider than what it handles.
- **Impact:** causes bugs (silent no-op)
- **Effort:** S (for the guard); M if the hierarchy is split
- **Proposed fix:** Decide whether markets are portfolio members. Either way, separate the base types (for example an asset base versus a market base) so the portfolio accepts only what it handles. Also apply the decided rename `TradeDirection` → `AllowedTradeDirection`.
- **API impact:** breaking if markets move into the portfolio or the rename lands (decided).

### F-11: `Objective` is a closed composition; adding a term edits four modules

- **Lens:** C (open/closed)
- **Location:** `objective.py:59-77`, `objectives.py:10-26`, `model_builder.py:105-106`, `:141-142`, `variable_definitions.py:217`
- **Evidence:** trace T2b (7-8 files). The terms are fixed attributes (`profit`, `cvar`), so a new term changes the `Objective` schema, `build_objective`, and both builder branch lists. `Objective` also lacks the `frozen` config that every other domain model has.
- **Problem:** `ObjectiveTerm` is a base class but is not used polymorphically. The optimization layer dispatches on attribute names rather than asking each term for its contribution.
- **Impact:** blocks extension
- **Effort:** M
- **Proposed fix:** `Objective` holds a collection of terms. Each term type maps to one model-side contribution (its expression, plus any variables and constraints it needs, as CVaR does today). This has two users today (profit and CVaR).
- **API impact:** breaking (`Objective` construction). Make it frozen.

### F-12: linopy is used directly across the optimization, solver and results layers; there is no modeling-layer boundary

- **Lens:** B (dependency inversion)
- **Location:** 17 modules (trace T3), for example `constraints_group.py:49`, `model_constraint.py:16`, `storage_constraints.py`, `milp_model.py`, `objectives.py`, `solver.py:37-48`, `optimization_results.py:4`
- **Evidence:** trace T3: a second modeling layer means rewriting all constraint code. Results import `linopy.constants` for status enums.
- **Problem:** High-level policy (what the constraints are) depends directly on one concrete library. This is only a problem if a second modeling layer is realistic. Per `AGENTS.md`, abstractions need two concrete users, and there is one today.
- **Impact:** blocks extension only for scenario T3
- **Effort:** L (full abstraction), S-M (containment)
- **Proposed fix:** **Do not abstract linopy now.** Record linopy as a deliberate platform choice. Contain it instead: linopy types stay inside `optimization/`; results and the public API use odys-owned status types and xarray/pandas only (see F-13). Revisit if a second modeling layer is ever planned.
- **API impact:** none

### F-13: The solver builds results, and results reach back into internal model structures

- **Lens:** B, D
- **Location:** `solver.py:43-49`; `optimization_results.py:8-9`, `:42-64`, `:95-173`
- **Evidence:** sequence 4.2 (solver lifeline creates results); import graph: `solvers → results`, and `results → parameters`, `results → optimization.model` (`VariableDefinitionRegistry` for variable names, `ModelDimension`).
- **Problem:** Solving and shaping results are coupled. Results depend on internal naming (registry `var_name`s) and on the parameters bag, only to recover flexible-load base profiles. Changes to variable names or parameters break results.
- **Impact:** hurts readability (and couples layers)
- **Effort:** S
- **Proposed fix:** The solver returns a solve outcome (status, termination, solution, objective value) with odys-owned status types. The pipeline (F-04) asks each asset component to extract its own results from the solution.
- **API impact:** none, if result accessors keep their shape

### F-14: Results repeat the same container protocol six times, and the interfaces are inconsistent

- **Lens:** A, C
- **Location:** `dispatch.py:13-460`, `optimization_results.py:20-180`
- **Evidence:** 6 classes each implement `__getitem__`, `__iter__`, `__len__`, `__contains__`, `to_dataset`, `to_dataframe` and `__repr__` (~75 lines each). `__getitem__` hard-codes dimension keywords (`sel(generator=key)`) instead of using `ModelDimension`. `MarketDispatch.net_volume` returns `xr.DataArray` while every other property returns `pd.Series` (`:373`). `OptimalDisptachResults` needs a property, a flag and a slot per asset type. Its name is misspelled, and it is returned to users without being exported.
- **Problem:** Duplication, plus small interface inconsistencies users will trip over. Adding an asset adds another copy.
- **Impact:** hurts readability
- **Effort:** M
- **Proposed fix:** One generic dispatch base implementing the container protocol over an asset dimension, with per-asset subclasses declaring only their series (6 users). Make return types consistent. Rename to `OptimalDispatchResults` and export it.
- **API impact:** breaking for the rename and for the `net_volume` return type

### F-15: Dimensions and coordinates live in `optimization.model` but are shared by all layers; `CoordinatesStore` duplicates `ModelDimension`

- **Lens:** B, A
- **Location:** `dimensions.py:6`, `coordinates.py:27-65`, `electric_vehicle_parameters.py:40`, `energy_system.py:136-167`
- **Evidence:** import graph: package-level cycles `parameters ⇄ optimization.model`; `dimensions` has fan-in 19. `CoordinatesStore` has one field per dimension plus a hand-written dimension-to-field mapping (`:51-60`). `ElectricVehicleParameters` builds its own time coordinates (`str(t)` at `:40`) instead of using the store. Integer versus string time coordinates are a known bug class that silently masks constraints (`AGENTS.md`).
- **Problem:** The shared vocabulary (dimensions, coordinates) sits inside one consumer layer, which causes the cycles. The store's per-dimension fields are another lockstep site. Time coordinates have more than one source of truth.
- **Impact:** causes bugs (a second time-coordinate source risks the masking bug class) and blocks extension
- **Effort:** M
- **Proposed fix:** Move dimensions and coordinates into a small shared module below `parameters`. Make the coordinate store a mapping keyed by dimension with one constructor for time labels, so every array gets time coordinates from one place.
- **API impact:** none

### F-16: `EnergySystemParameters` does not name or bound its responsibility

- **Lens:** A
- **Location:** `energy_system_parameters.py:22-41`
- **Evidence:** checkpoint 1 decision 4. It is aggregated by the builder, `EnergyMILPModel`, all constraint groups (indirectly) and results. It mixes a domain object (`Objective`), a scalar (`timestep`), coordinates and six optional per-asset blocks.
- **Problem:** The name says which layer it comes from, not what it is. Its optional-per-asset fields are another lockstep site (F-01).
- **Impact:** hurts readability
- **Effort:** M
- **Proposed fix:** Decide in Phase 3 together with F-01. It likely becomes "the input data of one optimization problem": horizon, coordinates, the collection of asset components, scenario data and objective terms. The name should state that meaning.
- **API impact:** none (internal)

### F-17: `*Parameters` classes restate entity fields by hand, three times per field

- **Lens:** A, B
- **Location:** `generator_parameters.py:27-88`, `standalone_storage_parameters.py:27-100`, `electric_vehicle_parameters.py:42-159`, `market_parameters.py:27-52`, `charger_parameters.py:27-46`, `flexible_load_parameters.py:27-52`
- **Evidence:** each field appears in the entity, in the `data` dict, and as a property. Names drift (`ramp_up` → `max_ramp_up` at `generator_parameters.py:37`, `max_trading_volume_per_step` → `max_volume` at `market_parameters.py:30`). There is no common base, so the shape is shared by convention only.
- **Problem:** Boilerplate that must follow every entity change, with renames that make the same quantity carry two names.
- **Impact:** hurts readability
- **Effort:** M
- **Proposed fix:** Vectorize an entity collection into a dataset generically from its fields, keeping hand-written accessors only for derived arrays (EV trip arrays, capacity profiles). Keep the same names across layers.
- **API impact:** none

### F-18: Ubiquitous-language and naming inconsistencies

- **Lens:** A
- **Location:** `base.py:12` (`EnergyEntity`, while the portfolio, docs and `AGENTS.md` say "asset"); `market.py:10` (`TradeDirection`; decided: `AllowedTradeDirection`); `optimization_results.py:20` (`OptimalDisptachResults`); `energy_system.py:98`, `:118` (`collection_of_scenarios`, `collection_of_markets`); `coordinates.py:10` (`ModelCoordinates` declared `ABC` but concrete); constraint methods named `_get_*` (private-looking but they are the group's contract)
- **Evidence:** inventory 2 and 7.13; checkpoint 1 decision 3.
- **Problem:** The same concept has different names across code and docs, and some names mislead (private-looking public methods, an abstract base that is instantiated).
- **Impact:** hurts readability
- **Effort:** S
- **Proposed fix:** Agree on a glossary in Phase 3 (asset, market, component, profile, dispatch) and apply it in one renaming step.
- **API impact:** breaking for public renames (`AllowedTradeDirection`, the results class)

### F-19: User inputs that are accepted and silently ignored

- **Lens:** A; illegal states representable
- **Location:** `charger.py:24-30` (`Charger.efficiency`: vectorized at `charger_parameters.py:31` but used in no constraint); `solver_config.py:33-36` (`SolverConfig.solver_options`: read nowhere, although documented as "override translated common options"); `portfolio.py:32` (markets in the portfolio, F-10)
- **Evidence:** `grep` for `.efficiency` and `solver_options` across `src/` finds no consumer.
- **Problem:** The public API promises behaviour that does not happen. Users get no error and a different model than they described.
- **Impact:** causes bugs
- **Effort:** S
- **Proposed fix:** Implement each field or remove it. This does not depend on the redesign. It is a candidate for the `fix-bug` workflow now.
- **API impact:** breaking only if a field is removed

### F-20: `EnergySystem` takes union-typed inputs and re-normalizes them on every access

- **Lens:** A (interface clarity)
- **Location:** `energy_system.py:77-78`, `:98-125`
- **Evidence:** `markets: EnergyMarket | Sequence[EnergyMarket] | None` and `scenarios: Scenario | Sequence[StochasticScenario]`. `collection_of_scenarios` builds a new `StochasticScenario` on every call, and it is called from validation and twice from `build_parameters`. `field_validator` validates probabilities only when the input is a `list` (`:83`). Verified: passing the same scenarios as a `tuple` with probabilities 0.7 + 0.7 is **accepted** (the list form is rejected), so probability-sum and unique-name checks are bypassed.
- **Problem:** Two input shapes per field make the interface harder to describe, push normalization into properties that run repeatedly, and have already produced a validation hole.
- **Impact:** causes bugs
- **Effort:** S
- **Proposed fix:** Normalize once at construction (a validator that stores tuples), or accept one shape per field. Deterministic runs could use a helper that creates the single-scenario collection.
- **API impact:** possibly breaking, depending on the accepted shapes

---

## 5. Cross-cutting themes

Grouping the findings shows the Phase 3 design questions:

1. **The asset as the unit of design** (F-01, F-02, F-03, F-05, F-06, F-07, F-15, F-16, F-17): what one asset-owned object on the model side looks like, and how it relates to its domain entity.
2. **Composition for shared physics** (F-08): battery as a value object and a reusable model component.
3. **Exogenous data** (F-09): how scenarios attach time series to assets without a field per asset kind.
4. **Actors versus assets** (F-10, T2a): where markets and future products sit, and how cross-asset capabilities (headroom) are declared once.
5. **Objective as open composition** (F-11).
6. **Boundaries and pipeline** (F-04, F-12, F-13, F-14, F-20): problem definition, pipeline, solve outcome, results; linopy contained, not abstracted.
7. **Language** (F-18, decided renames).

---

## 6. Prioritization

Mapping per the methodology matrix (bugs or extension-blocking: S→1, M→2, L→3; readability: S→2, M→3, L→backlog):

| Roadmap phase | Findings |
| --- | --- |
| **Phase 1** (do first) | F-10 (guard only), F-19, F-20 |
| **Phase 2** | F-02, F-03, F-05, F-06, F-07, F-11, F-13, F-15, F-18 |
| **Phase 3** (plan carefully) | F-01, F-04, F-08, F-09, F-14, F-16, F-17; F-12 containment only |
| **Backlog** | F-12 full modeling-layer abstraction (only if a second modeling layer is planned) |

Dependencies that will reorder this in Phase 4: F-05, F-06, F-07, F-15, F-16 and F-17 are cheaper done *as part of* F-01 than before it, and F-08 should land together with or right after F-01.

---

## 7. Out-of-scope bugs found during the review

Not architecture findings (the methodology excludes model mathematics), but real defects. Each should go through the `fix-bug` skill independently of the redesign.

1. **Probability sum uses exact float equality** (`scenarios.py:83`). Verified: on Python 3.11 (supported), `sum([0.1] * 10) == 1.0` is `False`, so ten equiprobable scenarios are rejected. Python 3.12+ sums floats more accurately, so the check passes there, making this a version-dependent bug.
2. **Timestep scaling in `per_scenario_profit` is inconsistent** (`milp_model.py:108-150`). Storage and EV degradation are multiplied by `timestep_hours`, while generator costs, flexible-load value and market revenue are not. `EnergyMarket.max_trading_volume_per_step` is described as "energy (in MW)" (`market.py:41`), so the unit of market volume is ambiguous. Results are consistent only when `timestep = 1h`. This needs a units review.
3. **`Charger.efficiency` is ignored** (F-19).
4. **`SolverConfig.solver_options` is ignored** (F-19).
5. **Scenario validation is bypassed for non-list sequences** (F-20). Verified: `EnergySystem(..., scenarios=(s1, s2))` with probabilities 0.7 + 0.7 is accepted, while the same list is rejected.

---

## 8. Checkpoint 2: questions for the user

Please confirm, dispute, or reclassify findings. These decisions shape Phase 3 the most:

1. **F-01:** Do you agree that the target is one model-side *asset component* per asset type that owns coordinates, parameters, variables, constraints, balance and profit contributions, and results, with domain entities staying free of xarray and linopy?
2. **F-08:** Should `ElectricVehicle` and `StandaloneStorage` *have* a `Battery` (composition), replacing the `Storage` base class?
3. **F-10 / T2a:** Should markets become portfolio members (with a separate base type), or stay a separate input to `EnergySystem`?
4. **F-12:** Do you accept linopy as a deliberate platform (contain it, don't abstract it)?
5. **Section 7:** Should the five out-of-scope bugs be fixed now on a separate branch, before the redesign?

---

## 9. Checkpoint 2 decisions

Recorded from the user's review (2026-09-30).

1. **F-01 (asset components):** agreed in principle. The design is deferred until decisions 2-4 are settled, and Phase 3 works it out.
2. **F-08 (storage):** `ElectricVehicle` and `StandaloneStorage` **have** a `Storage` (a battery) instead of inheriting from it. Composition replaces the `Storage` base class.
3. **F-10 (markets):** the portfolio holds only entities **owned by the user** (generators, storage, loads, EVs, chargers, and future thermal assets). Markets are not portfolio members. They stay a separate input, and the portfolio must reject them (a separate base type for owned assets versus markets).
4. **F-12 (linopy):** linopy is a **deliberate platform decision**. Contain it inside `optimization/`, but do not abstract it.
5. **Section 7 bugs:** fix them before the redesign, on a separate branch.

### Status of the section 7 bugs (2026-10-01)

Fixed on branch `fix/review-bugs` (git worktree `../odys-review-bugs`, based on `main`), each with a regression test that fails without the fix. Not yet committed.

| Bug | Resolution |
| --- | --- |
| 1. Probability sum | `math.isclose` tolerance; test with 49 × `1/49` |
| 2. Timestep scaling | Generator variable cost, market revenue and flexible-load value × Δt (startup and shutdown stay per event); docs formula and CHANGELOG updated (breaking for results when Δt ≠ 1h) |
| 3. `Charger.efficiency` | Left as a TODO at the field, per user decision; listed under "Known issues" in CHANGELOG |
| 4. `solver_options` | Merged over translated options |
| 5. Tuple scenarios | Validator checks any non-`Scenario` input; tests for list and tuple, for both sum and duplicate names |
