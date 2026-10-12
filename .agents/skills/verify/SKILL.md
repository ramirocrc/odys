---
name: verify
description: Run odys' Definition of Done checks (just check, just test, and just docs-build when docs/examples/public API changed) and report failures. Use before saying any code change is done, before committing, and before opening a PR.
---

# Verify (Definition of Done)

Run the checks below from the repo root and report the results honestly. Never claim a change is done while any of them fail.

## 1. Decide what to run

```bash
git status --short
git diff --name-only HEAD
```

- Always run steps 2 and 3.
- Also run step 4 if anything under `docs/`, `examples/`, `README.md`, `src/odys/__init__.py`, or any public docstring changed.

## 2. Static checks

```bash
just check
```

This runs the lock check, prek (ruff format/lint, pyupgrade, vulture, uv-secure), ty, pyrefly, basedpyright, zuban (strict), complexipy, import-linter, and deptry.

## 3. Tests and coverage

```bash
just test
```

Coverage must stay at or above 90%. `tests/test_escape_hatches.py` fails on any new suppression or escape hatch. To iterate on one failure: `uv run python -m pytest <path>::<test> -x -q`.

## 4. Docs (conditional)

```bash
just docs-build
```

## 5. Definition of Done checklist

Check the diff (`git diff HEAD`) against the rest of the Definition of Done in `AGENTS.md`:

- [ ] New behaviour has tests; bug fixes have a regression test that failed before the fix.
- [ ] No new `# noqa` / `# type: ignore` / `# pyright: ignore` / `# pyrefly: ignore` / `# ty: ignore` / `# complexipy: ignore` / `# pragma: no cover`, no `Any`, no `cast`, no skipped tests.
- [ ] No weakened config in `pyproject.toml`, `justfile`, `.pre-commit-config.yaml`, `noxfile.py`, or `.github/workflows/`, and no raised count in `ALLOWED_ESCAPE_HATCHES` (`tests/test_escape_hatches.py`) without a reason in the PR.
- [ ] Public API changes are exported in `odys/__init__.py` `__all__`, documented, and in `CHANGELOG.md`.

## 6. Report

Summarize in a short table: check → pass/fail. For each failure give the first error with its `file:line` and the fix you propose or applied. If something was skipped, say so and why.
