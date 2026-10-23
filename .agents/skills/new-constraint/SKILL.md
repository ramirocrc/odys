---
name: new-constraint
description: Checklist for adding or changing a constraint (and any variable it needs) on an existing odys asset or in power balance. Use whenever the task is a new constraint method, a new decision variable, or a change to constraint math. For a whole new asset type use add-asset instead.
---

# Add or change a constraint

Mirror `src/odys/optimization/formulations/flexible_load.py` and `tests/unit/test_optimization/formulations/test_flexible_load_formulation.py`. Read the Optimization section of "Layer rules" in `AGENTS.md` first. Every asset type is a formulation in `optimization/formulations/`; battery constraints shared by battery storage and EVs are methods of `StorageFormulation` (`formulations/storage.py`).

Before starting, confirm the math with the user: the constraint in equation form, the units, and which dimensions it ranges over.

## 1. Test first

- [ ] Add a test in the matching `tests/unit/test_optimization/formulations/test_<asset>_formulation.py`. Build the expected constraint with linopy expressions and compare using `assert_conequal`.
- [ ] Assert nothing is masked: `assert bool((constraint.labels != -1).all())`.
- [ ] Run it and watch it fail for the right reason.

## 2. Parameters and variables (only if needed)

- [ ] New input data: add an `xr.DataArray` field, named exactly like the domain field, to the asset's `*Arrays` class in `parameters/entity_arrays.py` (`vectorize` fills it). Time coordinates come from `context.time`, never hand-built `str(t)`.
- [ ] New variable: add a field to the formulation's typed variables object and create it in `_create_variables` (for a battery variable, in `StorageVariables` / `StorageFormulation.create_variables`).

## 3. Constraint

- [ ] Add a private method to the asset's formulation returning `ModelConstraint` (or `list[ModelConstraint]`) and list it in its `constraints()` (spread a list with `*`); for battery physics add a `StorageFormulation` method and list it in the `constraints()` of both storage formulations.
- [ ] Name it `<asset>_<what>_constraint`; it must be unique across the model.
- [ ] Stay vectorized over xarray dimensions. Use `ModelDimension` for scenario and time and the formulation's dimension constant for its entity axis, never string literals.
- [ ] If it changes power balance or profit, update the formulation's `power_injection()` / `profit()`.
- [ ] If a new variable should appear in results, add it under a short series name in the formulation's `dispatch()` (read by its `ClassVar` variable name), add a typed property on its `Dispatch` subclass in `results/dispatch.py`, and test the property in `tests/unit/test_results/test_dispatch.py` and the series in `tests/unit/test_optimization/test_dispatches.py`.

## 4. Verify

- [ ] Add or extend an integration test in `tests/integration/` that solves a small model and checks the dispatch.
- [ ] Follow the `verify` playbook.
