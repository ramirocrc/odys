---
name: add-asset
description: Step-by-step checklist for adding a new asset type (e.g. heat pump, electrolyzer) to odys across domain, parameters, variables, constraints, power balance, results, tests, and docs. Use whenever a new asset type or a new asset dimension is being introduced.
---

# Add a new asset type

Adding an asset touches many modules. Work through the steps in order, running the fast checks (`uv run pytest tests/unit -x -q`, `uv run ty check`) after each step. Mirror the closest existing asset (Generator for dispatchable supply, StationaryStorage for SOC-based assets, composing a `Battery` rather than re-declaring its fields, FlexibleLoad for demand-side assets) instead of inventing new patterns.

Before starting, confirm with the user: the asset's name, its user-facing parameters and units, its decision variables, its constraints (in math), and how it enters power balance and profit.

## 1. Domain (`src/odys/domain/`)

- [ ] Entity in `domain/entities/<asset>.py`: subclass `Asset` (user-owned) or `EnergyEntity` (external, like markets), pydantic `Field` constraints (`gt`, `ge`, …) with descriptions and units, and `model_validator`s for cross-field rules. Raise `OdysValidationError`.
- [ ] Callers get the new assets with `portfolio.assets_of(<Asset>)`; `AssetPortfolio` needs no change.
- [ ] Capability queries on the entity, so the generic rules in `domain/validation.py` cover it: override `max_supply` (injects power), `min_demand` (must withdraw power), `max_energy_supply` (energy-limited, like a battery) or `validate_horizon` (depends on the horizon, like EV trips). Each takes `OperatingConditions` (horizon plus the entity's profile values). Add a rule to `validation.py` only if it is genuinely system-level and not expressible through these.
- [ ] Per-scenario profiles: reuse a `Profile` subclass from `domain/profiles.py` (widen its entity field and `entity_types`) or add one that references the new asset, with `entity_types` and `required` ClassVars, a validator for single-profile rules, an entry in `PROFILE_TYPES` and in the `AnyProfile` union; export it and read it in the asset's formulation with `context.profiles(...)`.
- [ ] Initial and final conditions, if the asset carries state across the horizon (output, state of charge): add `<Asset>InitialState` / `<Asset>FinalState` to `domain/conditions.py` (subclass `InitialCondition` / `FinalCondition`, set `entity_types`, implement `required_for`), add them to `AnyInitialCondition` / `AnyFinalCondition` and `INITIAL_CONDITION_TYPES`, export them, and read them in the `*Arrays` builder with `context.conditions(...)`.
- [ ] Export from `src/odys/__init__.py` and add it to `__all__`.

## 2. Parameters (`src/odys/parameters/`)

- [ ] In `entity_arrays.py`, add an `EntityArrays` subclass with one `xr.DataArray` field per entity field the model reads, named exactly like the domain field. Add it to the parametrized `test_arrays_fields_are_fields_of_their_model` in `test_vectorize.py`.
- [ ] Any array with a time dimension takes its coordinates from `context.time`; never build `str(t)` labels. Read scenario profiles with `context.profiles(...)`.

## 3. Formulation (`src/odys/optimization/formulations/<asset>.py`)

Mirror `formulations/flexible_load.py`. The asset needs no builder or power-balance branch, no `ModelDimension` member and no coordinates entry anywhere else.

- [ ] A `Formulation` subclass that names its axis with a module constant (`<ASSET> = "<asset>"`, then `dimension = <ASSET>`; it must differ from every other formulation's and from `scenario`/`time`, which `test_problem.py` checks) and sets `entity_type = <Asset>`, so `validate_entities_supported` accepts the asset.
- [ ] A `build(inputs: FormulationInputs)` classmethod that picks its assets with `inputs.of_type(<Asset>)` (returns `None` when there are none; a formulation that depends on another reads it with `inputs.formulation_of(...)` and comes after it in `FORMULATIONS`), and an `__init__` that calls `super().__init__(assets, context)` (which builds `self.coordinates`) and vectorizes them (`vectorize(<Asset>Arrays, assets, self.coordinates)`).
- [ ] If the asset has decision variables, subclass `VariableFormulation[<Asset>Variables]` with a frozen typed variables object and implement `_create_variables(model)` (use `self.context.variable_coords(self.coordinates)`); the base provides `variables` and the one-model guard. Keep each linopy variable name as a `ClassVar` constant (`<asset>_power_name`) for results.
- [ ] One `@constraint` method per equation, returning `ModelConstraint` with a unique name ending in `_constraint`, reading only `self.arrays` and `self.variables`. Keep it vectorized. For SOC-style assets, compose `StorageFormulation` (`formulations/storage.py`) and delegate to its constraint methods, as `StationaryStorageFormulation` does.
- [ ] `power_injection()` (net power into the bus, summed over the asset dimension; put variable terms before constants) and `profit()` (per scenario, energy terms multiplied by `context.timestep_hours`), or `None` when the asset has none.
- [ ] Add the class to `FORMULATIONS` in `formulations/__init__.py`, and its module to the import-linter independence contract in `pyproject.toml` (a tool configuration change: say why in the PR).

## 4. Results (`src/odys/results/`)

- [ ] Add a `<Asset>Dispatch(Dispatch)` view in `dispatch.py` with `__slots__ = ()`, a `label` (`"<asset>"`, used in the "does not contain" error) and one typed property per series returning `self._series("<name>")`. The base already implements `__getitem__`, iteration, `to_dataset`, `to_dataframe` and `__repr__`. A battery-bearing asset subclasses `BatteryDispatch`.
- [ ] Implement `dispatch(solution)` on the formulation: build an `xr.Dataset` with the short series names from the `ClassVar` variable names (`"power": solution[self.power_name]`), compute derived series there, and return `<Asset>Dispatch(data, <ASSET>)` (or `None` if the asset has no results).
- [ ] Expose it on `OptimalDispatchResults` in `optimization_results.py` with one property: `return self._dispatch_of(<Asset>Dispatch)`.

## 5. Tests

- [ ] `tests/unit/test_domain/entities/test_<asset>.py`: valid construction, every field constraint, and every validator (use `Model.model_validate({...})` for invalid input).
- [ ] `tests/unit/test_optimization/parameters/test_<asset>_arrays.py`: shapes, coordinates, values.
- [ ] `tests/unit/test_optimization/formulations/test_<asset>_formulation.py`: each constraint exists, has the right coefficients, and has no masked entries (`assert bool((c.labels != -1).all())`); power injection and profit (`assert_linequal`); variables before `add_variables` raise.
- [ ] `tests/integration/`: an end-to-end solve that checks dispatch against a hand-computed optimum.
- [ ] `tests/unit/test_results/test_dispatch.py`: the new dispatch view (use test names prefixed with the asset, e.g. `test_<asset>_getitem`).

## 6. Docs and changelog

- [ ] User guide page in `docs/user_guide/`, API pages in `docs/developer/api/` (entity and formulation), and nav entries in `zensical.toml` (read `DOCS_GUIDELINES.md` first).
- [ ] The asset's variables and constraints in `docs/user_guide/mathematical_notation.md`, using the existing notation.
- [ ] The entity, its formulation and its dispatch in the class diagrams of `docs/developer/data_model.md`, with their inheritance edges (`tests/test_architecture_docs.py` fails until they are there).
- [ ] An example in `examples/` if the asset enables a new use case.
- [ ] A `CHANGELOG.md` entry.
- [ ] Update the "Adding a new asset type" list in `AGENTS.md` if the steps changed.

## 7. Finish

Follow the `verify` playbook, then the `review` playbook.
