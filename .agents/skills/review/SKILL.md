---
name: review
description: Self-review checklist for an odys change before opening a PR. Reviews the diff for design, layering, readability, modern-Python idioms and AGENTS.md conventions, then audits the tests for meaningful coverage. Use after a feature, refactor or bug fix is implemented and verified, and before opening a PR.
---

# Review a change before opening a PR

Review the diff like a strict senior reviewer would, then fix what you find. Do not report anything the tooling already enforces (ruff `ALL`, ty, pyrefly, basedpyright strict, zuban strict, complexipy, import-linter, vulture, `tests/test_escape_hatches.py`). Focus on what tools cannot judge.

## 1. Scope

- [ ] Get the diff: `git diff HEAD --stat` and `git diff HEAD`, or `git diff main...HEAD` if the working tree is clean. Review only changed code, but read enough surrounding code to judge it.
- [ ] Read `AGENTS.md`. It is the standard.
- [ ] Open the golden file (`AGENTS.md`, "Golden files") for each layer the diff touches. Flag new code that departs from its structure, naming, or docstring style without a reason. Never cite older code that predates these rules as precedent.

## 2. Code

**Design and architecture**

- [ ] Responsibilities sit in the right layer, and packages import only lower layers (`AGENTS.md`, "Architecture layers").
- [ ] Validation happens at construction (pydantic validators, `domain/validation.py`), not inside the formulations or constraints.
- [ ] Existing patterns are reused, not reinvented: one `constraints()` method listing the constraints, typed `*Variables` objects created in `_create_variables` at the end of `__init__`, `Formulation` / `ObjectiveTermFormulation` and their registries, `*Arrays` + `vectorize`, `ModelContext`, a `Dispatch` subclass built by the formulation's `dispatch()`, `SolveOutcome.has_solution`.
- [ ] No speculative abstractions: no new base class, protocol, registry, flag or parameter without two concrete users.
- [ ] No duplication that should be one function, and no helper that exists for one call site and hurts readability.
- [ ] Everything new in `__all__` is meant to be public, and no linopy or xarray internals leak into the public API (results excepted).

**Readability and naming**

- [ ] Names state intent and units (`max_charge_power`, not `p_max`), with no abbreviations beyond domain-standard ones (SOC, CVaR, EV).
- [ ] Each function does one thing at one level of abstraction; no comments that explain "sections" (split the function instead).
- [ ] Google-style docstrings explain *why* and units, not a restatement of the signature.

**Modern Python (3.11+)**

- [ ] `X | None`, `Self`, `StrEnum`, `match` where it clarifies, `collections.abc` types in signatures, keyword-only boolean flags, frozen pydantic models, `pathlib`.
- [ ] No mutable default arguments, no bare `except`, no catching `Exception` without re-raising a typed `Odys*` error, and `raise ... from err` for chained errors.

**Correctness smells specific to odys**

- [ ] Time coordinates come from `context.time` (strings); integer coordinates silently mask constraints.
- [ ] No Python loops over timesteps or assets where an xarray expression works.
- [ ] No hard-coded dimension strings: `ModelDimension` for scenario and time, the formulation's `dimension` constant for its entity axis.
- [ ] Linopy variable names are read only by the formulation that owns them (results get series from `dispatch()`).
- [ ] "Is there a solution" is decided by `has_solution`, not the solver status (linopy reports `ok` for a time limit with no incumbent).
- [ ] `Odys*` errors, not generic `ValueError` / `TypeError`, and no floating-point equality in model logic.

## 3. Tests

- [ ] Find the tests of each changed unit (`tests/unit/` mirrors `src/odys/`; end-to-end tests are in `tests/integration/`) and run them with branch coverage, e.g. `uv run python -m pytest tests/unit/<area> -q --cov=src/odys/<module> --cov-branch --cov-report=term-missing`. Note uncovered changed lines and branches.
- [ ] Every new public function, validator, constraint and error path has a test asserting its observable effect, not just "no exception".
- [ ] Assertions are meaningful: no tautologies, floats compared with `pytest.approx` / `xarray.testing`, `pytest.raises(OdysValidationError, match=...)` checks the message.
- [ ] Edge cases for this domain: one vs. several scenarios; scenario probabilities; zero or empty profiles; zero capacity; assets absent from the portfolio (formulation not built, results raise `OdysNoResultsError`); a solve without a solution; first and last timestep; missing or inconsistent initial and final conditions; trips at horizon boundaries; infeasible systems; CVaR on and off; `stage_fixed` markets.
- [ ] Constraint tests check coefficients and bounds, and assert no masked entries for time-indexed parameters.
- [ ] Integration tests check the solved dispatch against a hand-computable optimum, not just "status is optimal".
- [ ] Conventions from the Testing section of `AGENTS.md` hold, and test names are unique within a module (a shadowed duplicate never runs).
- [ ] No removed or loosened assertion, no new `skip` / `xfail`, no widened tolerance.

## 4. Act on the findings

Sort findings into **Must fix** (bugs, layering violations, convention breaks, missing tests), **Should fix** (design, readability, weak tests) and **Consider** (optional polish), each with `path:line`, the problem in one sentence and a concrete change. Fix every Must fix item, then follow the `verify` playbook again. Mention any Should fix item you leave in the PR description.
