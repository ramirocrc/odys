# AGENTS.md

Guidance for coding agents (and humans) working on odys. It is the single source of truth: the step-by-step playbooks in `.agents/skills/` build on it, and `CONTRIBUTING.md` covers the human workflow.

## Project Overview

Odys is a Python library for optimizing multi-asset energy portfolios across multiple electricity markets using stochastic optimization.

User workflow: define assets (Generator, StationaryStorage and ElectricVehicle (each with a `Battery`), FixedLoad, FlexibleLoad, Charger, Trip) and markets (EnergyMarket) → group them in an `AssetPortfolio` → describe each possible future as a `Scenario` holding typed profiles (`LoadProfile`, `AvailableCapacityProfile`, `PriceProfile`) that reference their asset or market → create `EnergySystem` (with `initial_conditions` / `final_conditions` for assets that carry state across the horizon) → call `.optimize()`. Stochastic optimization is the default; a single `Scenario` (name `"base"`, probability 1) becomes a one-element `ScenarioSet`.

The full public API is what `odys/__init__.py` re-exports (`__all__`). Anything not in `__all__` is internal and may change freely.

## Development Commands

```bash
just install               # Create venv with uv, install prek hooks
source .venv/bin/activate  # Activate virtual environment
just check                 # uv lock check + prek + ty + pyrefly + basedpyright + zuban + complexipy + import-linter + deptry
just test                  # pytest -n auto --cov (90% minimum coverage, branch coverage)
just docs                  # Serve docs locally (zensical serve)
just docs-build            # Generate example plots, run the User Guide code (tools/docs/check_user_guide.py), zensical build --strict --clean
just build                 # Build wheel + sdist, smoke test both
just examples              # Run all examples/*.py
just nox                   # Run nox sessions (integration tests, multiple Python versions)
```

CI runs: `just check` -> `just test` -> `just docs-build`

Other useful commands:

- Run a single test: `uv run python -m pytest tests/unit/test_domain/test_validation.py::test_name` (`just test` uses pytest-xdist `-n auto`; drop it when debugging a single test)
- `just nox` / `uvx nox` — integration tests across Python 3.11–3.14 with `highest` and `lowest-direct` dependency resolutions
- `just docs-assets` — regenerate the git-ignored docs assets: brand stylesheet, example plots and landing page data (`tools/docs/`, run by `just docs` and `just docs-build`)
- `just generate-logo` — regenerate the committed logo SVGs in `docs/assets/brand/` from Michroma (`tools/docs/generate_logo.py`)

## Definition of Done

A change is done only when all of these hold:

1. `just check` and `just test` pass locally. Do not claim success without running them.
2. New behaviour has tests; bug fixes start with a failing test that reproduces the bug.
3. No new suppressions or escape hatches (`# noqa`, `# ruff: noqa`, `# type: ignore`, `# pyright: ignore`, `# pyrefly: ignore`, `# ty: ignore`, `# complexipy: ignore`, `# pragma: no cover`, `Any`, `cast`, skipped/xfailed tests, ignored warnings), no removed or loosened test assertions, and no weakened tool configuration (ruff ignores, type checker modes, coverage threshold, import-linter contracts). `tests/test_escape_hatches.py` fails on any new escape hatch; never raise a count in its `ALLOWED_ESCAPE_HATCHES` to make it pass. If one seems unavoidable, stop and ask.
4. Public API changes are exported in `odys/__init__.py` `__all__`, have Google-style docstrings, and are reflected in `docs/` and `CHANGELOG.md`.
5. `just docs-build` passes when docs, examples, or public API changed.

## Playbooks

Step-by-step checklists for recurring tasks live in `.agents/skills/<name>/SKILL.md`. Read the matching one before starting:

| Task | Playbook |
| --- | --- |
| Add a new asset type | [`add-asset`](.agents/skills/add-asset/SKILL.md) |
| Add or change a constraint or decision variable | [`new-constraint`](.agents/skills/new-constraint/SKILL.md) |
| Fix a bug | [`fix-bug`](.agents/skills/fix-bug/SKILL.md) |
| Check the Definition of Done before saying a change is done | [`verify`](.agents/skills/verify/SKILL.md) |
| Self-review the diff and its tests before opening a PR | [`review`](.agents/skills/review/SKILL.md) |

## Code Style Guidelines

Most style is enforced by tooling (ruff `select = ["ALL"]`, four type checkers, complexipy, vulture). Rules below are the ones tools cannot fully check.

- **Type hints everywhere** — use `X | None` union syntax, not `Optional[X]`. Avoid `Any` and `cast`; model the type properly instead.
- **Pydantic frozen models** — use `ConfigDict(frozen=True, extra="forbid")` for all data classes
- **Custom exceptions** — never raise generic `ValueError`/`TypeError`:
  - `OdysError` — base exception
  - `OdysValidationError` — user input validation failures
  - `OdysSolverError` — solver failures or unexpected status
  - `OdysNoResultsError` — accessing results that don't exist
- **Line length**: 120 characters
- **Docstrings**: Google-style
- **No comments unless requested** — split into functions if you need comments to explain sections

## Design Principles

- **Small, single-purpose functions** with explicit inputs and outputs. Prefer pure functions over methods that mutate state.
- **Return typed objects, not dicts or tuples**, when a value has more than one field.
- **Explicit boundaries:** pydantic models at the user-facing edge (`domain/`), xarray inside the model (`parameters/`, `optimization/`). Do not leak linopy or xarray types into the public API except in results.
- **Dependencies point inward** (see Architecture layers). `domain/` knows nothing about optimization.
- **No speculative abstractions.** No base classes, protocols, registries, or config options without at least two concrete users.
- **Follow existing patterns** before inventing new ones: `ConstraintGroup` + `@constraint` for constraints, a typed variables object created in `_create_variables` for variables, `*Arrays` classes built by `vectorize` for parameters.
- **Make illegal states unrepresentable:** validate at construction (pydantic validators, `domain/validation.py`), not deep inside the model builder.

## Modern Python

Only what tools cannot check (ruff, the type checkers and `tests/test_escape_hatches.py` handle the rest):

- Use `StrEnum` for closed string sets, `match` when dispatching on an enum or a shape, and `Self` for methods that return their own type.
- Take abstract types in parameters (`collections.abc.Sequence`, `Mapping`) and return concrete ones.
- Boolean flags are keyword-only (`def f(x, *, strict: bool)`).
- Return small frozen models or `NamedTuple`s, never bare tuples or dicts with more than one field.
- Prefer early returns over nested `if`/`else`; prefer comprehensions and xarray operations over index loops.
- Chain errors with `raise OdysError(msg) from err`; put the message in a `msg` variable first.
- Name things for intent and units (`max_charge_power`, not `p_max`).
- Don't add `Any`, `cast`, or suppressions to make a checker pass; fix the type.

### Golden files

Imitate these when adding code. The FlexibleLoad slice is the smallest complete example of every layer.

| Layer | File |
| --- | --- |
| Domain entity | `src/odys/domain/entities/flexible_load.py` |
| Parameters | `src/odys/parameters/entity_arrays.py` (`FlexibleLoadArrays`) |
| Formulation (variables, constraints, power injection, profit, dispatch) | `src/odys/optimization/formulations/flexible_load.py` |
| Results view | `src/odys/results/dispatch.py` (`FlexibleLoadDispatch`) |
| Formulation tests | `tests/unit/test_optimization/formulations/test_flexible_load_formulation.py` |

Some older code predates these rules. Don't copy it.

## Architecture Flow

```
Assets → AssetPortfolio → EnergySystem (validates on init)
→ EnergySystem.build_problem() → OptimizationProblem.assemble() → OptimizationProblem (context, formulations, objective terms)
→ build_model() → linopy.Model
→ solve(model, solver_config) (HiGHS by default) → SolveOutcome
→ OptimalDispatchResults(outcome, problem.dispatches) (each formulation's dispatch(solution), read only with a solution)
```

`EnergySystem.optimize()` is this pipeline: three calls, no separate optimizer object.

The class diagrams of the implemented design are in `docs/developer/data_model.md` and the `optimize()` sequence diagram in `docs/developer/sequences.md`; `tests/test_architecture_docs.py` fails when a public or core model class is missing from them, or when a diagram names a class, member or inheritance edge the code does not have. Update the diagram, not the test.

Details worth knowing (they take multiple files to piece together):

- The modeling layer is **linopy** (xarray-based algebraic modeling), not Pyomo/PuLP. `solve(model, solver_config)` (`src/odys/solvers/solver.py`) validates the requested solver against `linopy.available_solvers` (raising `OdysSolverError` if missing) and returns a `SolveOutcome` (`solvers/outcome.py`: odys-owned `SolveStatus`, termination condition, objective value, solution; without a solution, `None` and an empty dataset). Results are built from the outcome and never see linopy status types. Check `outcome.has_solution`, not the status: linopy also reports `ok` for a time limit reached before the first feasible solution. HiGHS ships by default via `highspy`; Gurobi/CPLEX/SCIP are optional extras.
- Solver choice is controlled by `SolverConfig` (with the `SolverName` enum: highs/gurobi/cplex/scip) in `src/odys/solvers/solver_config.py`, passed as `EnergySystem.optimize(solver_config=...)`. Defaults to HiGHS when omitted.
- The **objective** is an `Objective` (`domain/objective.py`) holding a tuple of `terms`: a required `ProfitTerm` and an optional `CVaRTerm`, at most one per type (read one with `objective.term_of(CVaRTerm)`); `Objective()` maximizes expected profit. Each term type has an `ObjectiveTermFormulation` in `optimization/objective_terms/` (`ProfitTermFormulation`, `CVaRTermFormulation`), listed once in `OBJECTIVE_TERM_FORMULATIONS`; like an entity formulation, it is built by `build(inputs: ObjectiveTermInputs)` only when the objective has its term, adds its own variables and `@constraint`s (CVaR's value at risk, shortfalls and `cvar_shortfall_constraint`), and returns its weighted `expression()`. The objective is the sum of the expressions; no code branches on the term type.
- **Formulations:** `optimization/formulations/` holds one `Formulation` per entity type (`GeneratorFormulation`, `EnergyMarketFormulation`, `FixedLoadFormulation`, `FlexibleLoadFormulation`, `StationaryStorageFormulation`, `ElectricVehicleFormulation`, `ChargingFormulation`), listed once in `FORMULATIONS` (build and power-balance order). Each names its own axis (`dimension = GENERATOR`, a module constant such as `"generator"`) and the entity type it models (`entity_type = Generator`), and the base `__init__(entities, context)` builds its `coordinates` (entity names along that axis); `validate_entities_supported` (`formulations/__init__.py`, called by `EnergySystem` on init) rejects an entity whose type no formulation models. A formulation is built by its `build(inputs: FormulationInputs)` classmethod (entities via `inputs.of_type(...)`, the context, and earlier formulations via `inputs.formulation_of(...)`) only when entities of its type exist, and owns its parameter arrays and scenario profiles (`context.profiles`), its `@constraint` methods (it is a `ConstraintGroup`), `power_injection()`, `profit()` and `dispatch(solution)` (its results view, `None` for fixed loads). Formulations with variables subclass `VariableFormulation[XVariables]`: `_create_variables(model)` returns a frozen typed variables object, `variables` raises before `add_variables`, and a second `add_variables` raises (one problem builds one model). Linopy variable names are `ClassVar` constants (`GeneratorFormulation.power_name`) that its `dispatch()` reads from the solution. Storage and EVs compose the stateless battery part `StorageFormulation` (`formulations/storage.py`, names prefixed with the dimension) and delegate their battery constraints to it; `ChargingFormulation` receives the `ElectricVehicleFormulation` (the one allowed import between formulations, declared in the import-linter contract) and returns `None` from `power_injection()` (outside the balance). `OptimizationProblem` (`optimization/problem.py`) holds the context, the formulations and the objective-term formulations, built by `OptimizationProblem.assemble(entities, horizon, scenario_set, objective)` (which `EnergySystem.build_problem()` calls); `problem.formulation_of(Type)` returns one, and `problem.dispatches(solution)` collects every formulation's dispatch.
- **Results:** `results/dispatch.py` holds the `Dispatch` base (one `xr.Dataset` of an entity type's series plus its dimension; `__getitem__`/`__iter__` return `Self`, `__len__`, `__contains__`, `to_dataset`, `to_dataframe`, `__repr__`, written once) and one subclass per type that only declares typed `pd.Series` properties and a `label` (`BatteryDispatch` is shared by stationary storage and EVs). A formulation builds its dispatch with short series names and computes derived series (charger power, flexible `actual_load`, market `net_volume`) there. `OptimalDispatchResults(outcome, build_dispatches)` squeezes a single scenario once and serves the typed properties (`results.generators`) through one lookup by dispatch type.
- **Parameters:** `assemble` builds one `ModelContext` (`parameters/context.py`: time and scenario coordinates, `timestep_hours`, `probabilities`, `profiles(kind, entities, coordinates)`); each formulation builds its typed `*Arrays` object with `vectorize(arrays_type, entities, coordinates)` (`parameters/vectorize.py`, `parameters/entity_arrays.py`). Array fields are named exactly like the domain fields. Formulations read their scenario profiles (`LoadProfile`, `AvailableCapacityProfile`, `PriceProfile`) through `context.profiles` and the run's initial and final conditions through `context.conditions`.
- **Coordinates:** labels live in `parameters/coordinates.py` (`Coordinates`): time and scenario on the context (`context.time`, `context.scenarios`), each entity axis on its formulation (`formulation.coordinates`). Time coordinates are **strings** (`"0"`, `"1"`, …) and `ModelContext.time` is their only producer. Parameter arrays with integer time coordinates align to nothing, and linopy silently masks every constraint that uses them.
- **Variables:** a formulation or objective term declares its own typed variables object (`GeneratorVariables`, `CVaRVariables`) and creates it in `_create_variables`. `VariableOwner` (`optimization/variable_owner.py`) holds it: `variables` raises before `add_variables`, and a second `add_variables` raises.
- **Model builder:** `build_model(problem)` (`optimization/model/model_builder.py`) returns a plain `linopy.Model`: variables of every formulation then every objective term, constraints of every formulation, `PowerBalance`, then every objective term, and the objective (sum of term expressions, maximized). Building one problem twice raises `OdysError` (the variable guard).
- **Constraints:** formulations, objective terms and `PowerBalance` subclass `ConstraintGroup` (`optimization/constraints/constraints_group.py`); methods decorated with `@constraint` return `ModelConstraint`s and are collected automatically in definition order. Shared battery dynamics (SOC, used by stationary storage and EVs) live in `formulations/storage.py`.
- **Power balance** is `PowerBalance` (`optimization/power_balance.py`): every formulation's `power_injection()` (in `FORMULATIONS` order, `None` skipped), equal to zero. A new entity type joins it by implementing `power_injection()`; no branch is added. `FixedLoadFormulation` has no variables; its injection is minus the summed demand.
- **Profit:** `per_scenario_profit(formulations)` (`formulations/base.py`) sums every formulation's `profit()`; the profit and CVaR objective terms use it.
- `EnergySystem` normalizes `scenarios` into a `ScenarioSet` (`domain/scenario.py`, which checks probabilities and unique names), `initial_conditions`/`final_conditions` into a `ConditionSet` (`domain/conditions.py`), `markets` into a tuple and `timestep`/`number_of_steps` into a `Horizon` (`domain/horizon.py`), once, then validates on init (`domain/validation.py`).
- **Validation is layered:** single-entity rules (EV trip overlap) are entity validators, single-profile rules (capacity within nominal power, flexible base ≥ `max_decrease`) are profile validators, and "chargers if and only if EVs" is an `AssetPortfolio` invariant. `validation.py` holds only generic system rules: they reach entities through the capability queries on `EnergyEntity` (`max_supply`, `min_demand`, `max_energy_supply`, `validate_horizon`, each taking `OperatingConditions`) and profiles through each `Profile` type's `entity_types` / `required` ClassVars, so a new asset type is covered by overriding those queries.
- `ModelDimension` (StrEnum, `parameters/dimensions.py`) holds only the shared axes: scenario (`Scenarios`) and time (`Time`). Entity axes are named by their formulation's `dimension`: generator, market, fixed_load (profiles only), flexible_load, stationary_storage, ev, charger. Use the constant (`GeneratorFormulation.dimension`, or the module constant inside its formulation), never a string literal.

### Architecture layers

Enforced by import-linter (`[tool.importlinter]` in `pyproject.toml`, part of `just check`):

- `odys.domain` imports nothing else from `odys`, and no `linopy`, `xarray`, `numpy`, or `pandas`.
- `odys.parameters` does not import `linopy`.
- `odys.parameters` imports only `odys.domain` (never `odys.optimization`, `solvers`, `results` or `energy_system`); `optimization` and `results` take dimensions, coordinates and the context from it.
- Packages import only lower layers: `energy_system` → `optimization` → `results` → `solvers` → `parameters` → `domain`. Formulations build their results views, so `optimization` imports `results`, never the reverse.
- `odys.optimization` must not import `odys.solvers`.
- `odys.results` does not import `linopy`; it reads the solve outcome (`odys.solvers.outcome`) and dimension names only.
- `odys.solvers` imports no model layer (`odys.parameters`, `optimization`, `results`, `energy_system`): it takes a `linopy.Model` and returns a `SolveOutcome`.
- `odys.energy_system` is the composition root.

### Layer rules

**Domain** (`src/odys/domain/`, golden file `entities/flexible_load.py`)

- User-owned entities subclass `Asset`, external ones (markets) subclass `EnergyEntity` (`entities/base.py`); both already set `ConfigDict(frozen=True, extra="forbid")`. Value objects without a name (`Battery`, `Trip`) subclass `BaseModel` and must set the same config.
- Prefer composition for shared physics: `StationaryStorage` and `ElectricVehicle` *have* a `Battery`; they don't inherit from a storage base class.
- Constrain fields with pydantic `Field(strict=True, gt=..., ge=..., description=...)`. Descriptions state the unit (MW, MWh, currency per MWh).
- Single-entity rules go in a `model_validator` on the entity; single-profile rules (values against the referenced entity) go in a `model_validator` on the profile; collection rules go on the collection (`AssetPortfolio`, `ScenarioSet`, `ConditionSet`). Rules that span entities and scenarios go in `validation.py` as one small generic function per invariant, called from `validate_energy_system_inputs`, and reach entities only through their capability queries (`max_supply`, `min_demand`, `max_energy_supply`, `validate_horizon`) and profile types only through `entity_types` / `required`. Never `isinstance`-dispatch on asset kinds there.
- Raise `OdysValidationError`, never `ValueError`/`TypeError`.

**Parameters** (`src/odys/parameters/`, golden file `entity_arrays.py`, `FlexibleLoadArrays`)

- `dimensions.py` (`ModelDimension`: only the shared `Scenarios` and `Time` axes), `coordinates.py` (`Coordinates`, whose `dimension` is a plain string) and `context.py` (`ModelContext`: time, scenarios, step length, probabilities, profiles, conditions) are the shared vocabulary of every layer. Entity axes and their coordinates belong to the formulations, so this layer never names an entity type's dimension.
- `ModelContext` is the **only** producer of time labels (`context.time`, strings `"0"`, `"1"`, …). Take time coordinates from it; never build `str(t)` yourself. Integer time coordinates silently mask every constraint that uses them.
- Entity parameters are typed `EntityArrays` subclasses in `entity_arrays.py`, built by `vectorize(arrays_type, models, coordinates)`. Each field is an `xr.DataArray` named **exactly** like the domain field it reads (no renames), and only fields the model reads are declared. Arrays that are not entity fields (EV trip arrays, values from the run's conditions) are built by hand from `context.time` and `context.conditions(...)`.
- Scenario profiles become arrays through `context.profiles(kind, entities, coordinates, default=...)`; don't read profiles by name.
- An empty entity sequence is an internal error (`vectorize` raises `OdysError`). `None` means "no such asset", decided in `OptimizationProblem.assemble()` (formulations are built only when entities of their type exist).
- Vectorize with xarray/numpy. Don't loop over timesteps or assets in Python unless the value is really per-element.

**Optimization** (`src/odys/optimization/`, golden file `formulations/flexible_load.py`)

- The step length is `context.timestep_hours` and the scenario probabilities are `context.probabilities`; don't recompute them.
- Use the dimension constants (`ModelDimension.Time`, `GENERATOR = "generator"` in its formulation module); never write a dimension name as a string literal.
- A formulation reads only its own arrays, variables and the context, never the whole model. Its results view is built in `dispatch(solution)` from its `ClassVar` variable names, with derived series computed there.
- `@constraint` methods return `ModelConstraint` (or `list[ModelConstraint]`). Constraint names must be unique across the model and end in `_constraint`.
- `PowerBalance` sums variable injections first and constant ones (fixed demand) after, because `xr.DataArray + linopy.LinearExpression` does not produce a linopy expression; keep variable terms first inside `power_injection()` too.
- linopy's `==` on expressions is typed as `bool` by some checkers. Build equality constraints with `expression.to_constraint("=", rhs)` (as `PowerBalance` does), so no suppression is needed.
- Keep constraints vectorized over xarray dimensions. Do not loop over assets or timesteps in Python unless the constraint is really per-element (e.g. trip-specific).
- Shared battery dynamics for stationary storage and EVs live in `StorageFormulation` (`formulations/storage.py`), a stateless part both compose; it takes the variables as an argument. Reuse it rather than duplicating.
- Raise `OdysError` subclasses, never `ValueError`.

### Adding a new asset type

Touches: entity (`domain/entities/`, subclass `Asset`, override the capability queries it needs) → public export (`__init__.py`) → profile type if it needs one (`domain/profiles.py`) → `*Arrays` class (`parameters/entity_arrays.py`) → `Formulation` subclass in `optimization/formulations/` (`dimension`, `entity_type`, arrays, typed variables, `@constraint`s, `power_injection()`, `profit()`, `dispatch()`) + an entry in `FORMULATIONS` → results (a `Dispatch` subclass with typed series properties in `results/dispatch.py`, one typed property in `optimization_results.py`) → tests → docs (including the entity, formulation and dispatch in the diagrams of `docs/developer/data_model.md`). Follow the `add-asset` playbook.

## Testing

- Unit tests live in `tests/unit/`, mirroring `src/odys/` (`test_domain`, `test_optimization/{formulations,objective_terms,model,parameters}`, `test_results`, `test_solvers`). Put new tests in the matching folder. Test modules need unique basenames across the tree (no `__init__.py`), e.g. `test_fixed_load_formulation.py` next to `test_domain/entities/test_fixed_load.py`. The `tests/` root holds checks on the repository rather than a module: `test_architecture_docs.py` (diagrams against the code), `test_escape_hatches.py` (no new suppressions), `test_agent_guidelines.py` (paths named in this file and the playbooks exist).
- Docs tests live in `tests/docs/`: the brand tokens, the landing page snippets and the committed logo SVGs. They run in `just test` but not in the `just nox` matrix, because they need the `docs` dependency group.
- Integration tests live in `tests/integration/`: they solve real models end to end and also run across Python versions with `just nox`. Use `@pytest.mark.parametrize` with factory functions there.
- Shared fixtures live in the nearest `conftest.py` (e.g. `unit/test_optimization/objective_terms/conftest.py`). Reuse them before adding new ones.
- Test data as module-level UPPER_CASE constants (e.g. `STANDARD_GENERATOR_POWER = 100.0`); no magic numbers inside test bodies.
- One behaviour per test. Name tests `test_<unit>_<condition>_<expected>`.
- Use `@pytest.mark.parametrize` (with `ids=`) instead of loops or copy-pasted tests.
- Assert on observable behaviour: constraint coefficients and bounds, solved dispatch values, raised `Odys*` exceptions (`pytest.raises(OdysValidationError, match=...)`). Do not test private helpers directly.
- Do not mock linopy, xarray, or the solver. Build small real models; HiGHS solves them in milliseconds.
  - Exception: outcomes a real solve cannot produce reliably may be simulated with `monkeypatch` on linopy, because the test is about how odys handles the outcome, not about the solver. The current cases are a solve that ends without a solution (`linopy.Model.solve` returning "infeasible", or `ok` with "time_limit" and no incumbent; `test_optimization_results.py`, `test_solver.py`) and a solver that is not installed (`linopy.available_solvers` emptied; `test_solver.py`). Add a case here before adding another such test.
- For constraints built from parameters with a time dimension, assert no masked entries: `assert bool((constraint.labels != -1).all())`.
- Compare floats with `pytest.approx` or `xarray.testing.assert_allclose`, never `==`.
- Coverage is at least 90%, with branch coverage.
- Never delete, skip, or loosen an existing assertion to make a test pass. If a test looks wrong, ask.

## Project Structure

- `src/odys/domain/` - User-facing entities, scenarios, objective, validation, exceptions
- `src/odys/parameters/` - Vectorization of domain entities into xarray data
- `src/odys/optimization/formulations/` - One `Formulation` per entity type
- `src/odys/optimization/objective_terms/` - One `ObjectiveTermFormulation` per objective term type
- `src/odys/optimization/model/` - The model builder
- `src/odys/optimization/constraints/` - The `ConstraintGroup` base, `@constraint` and `ModelConstraint`
- `src/odys/solvers/` - Solver configuration and invocation, returning a `SolveOutcome`
- `src/odys/results/` - `OptimalDispatchResults` and the per-type `Dispatch` views
- `src/odys/energy_system.py` - `EnergySystem`, the composition root
- `tests/unit/`, `tests/integration/`, `tests/smoke_test.py` (post-build smoke test), `tests/test_architecture_docs.py` (architecture diagrams against the code), `tests/test_escape_hatches.py` (no new suppressions), `tests/test_agent_guidelines.py` (guidance paths exist), `tests/docs/` (docs tooling checks)
- `.agents/skills/` - Playbooks for recurring tasks (see Playbooks)
- `examples/*.py` - Standalone example scripts
- `docs/` - Documentation content (built with zensical, config in `zensical.toml`; the landing page template is in `overrides/`)
- `tools/docs/` - Docs build tooling: asset generators, brand tokens, landing page snippets (see `tools/docs/README.md`)

## Key Libraries

- **linopy** — xarray-based linear/mixed-integer optimization modeling
- **highspy** — HiGHS MILP solver (via linopy)
- **xarray** — N-dimensional arrays (scenarios, time, assets dimensions)
- **pydantic** — data validation and immutable models

## Dependencies

- Python 3.11-3.14 supported (write code that runs on 3.11; `pyupgrade` and ruff target `py311`)
- deptry ignores `highspy` and the optional solver packages (DEP002) — do not add to dependencies without checking
- Never edit `uv.lock` by hand; use `uv add` / `uv lock`

## Pre-commit

- Pre-commit tooling is `prek` (a pre-commit reimplementation); hooks run ruff-format, ruff, pyupgrade, vulture, uv-lock, uv-secure
- `uv run --locked prek install` after cloning
- `uv run --locked prek autoupdate` to refresh hooks
- Lock file is checked on pre-commit via `uv-lock`

## Type Checking

`just check` runs four type checkers: `ty`, `pyrefly`, `basedpyright`, and `zuban` (strict). All must pass.

## Publishing

Releases are made by the maintainers. Never run `just publish` or `just build-and-publish`; `just build` (build + smoke test) is safe.

## Working Guidelines

- When asked to fix tests, only modify test files unless the user explicitly asks to modify the main codebase
- If a main code change is needed to fix tests, ask for permission before making it
- Do not add new functions, classes, or methods to the main codebase without explicit user request
- Plan before editing when a change touches more than two modules or changes the public API
- Never weaken a test, an assertion, or a tool configuration to make a check pass
- Keep diffs focused: no drive-by refactors or reformatting of unrelated code

## Documentation Style

- When working on docs, read `DOCS_GUIDELINES.md` (repo root) first
- Use **relative paths** for assets (images, iframes) in markdown files — never absolute paths starting with `/`. The site is served from `https://ramirocrc.github.io/odys/`, so absolute paths break on GitHub Pages. Example: use `../assets/examples/plot.html` instead of `/assets/examples/plot.html`
