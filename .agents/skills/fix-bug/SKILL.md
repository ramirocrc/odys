---
name: fix-bug
description: Test-first workflow for fixing a bug in odys. Use whenever the task is to fix incorrect behaviour, a wrong result, or a crash, so the fix starts from a failing regression test.
---

# Fix a bug

Definition of Done requires a failing test that reproduces the bug before the fix.

## 1. Reproduce

- [ ] Restate the bug as expected vs. actual behaviour. If either is unclear, ask the user.
- [ ] Find the layer where it first goes wrong (domain validation, parameters, constraints, the formulation's `dispatch()`, results). Check the odys-specific suspects first: integer time coordinates (silent masking), wrong dimension name (`ModelDimension` or a formulation's `dimension`), sign or unit errors, `None` vs. empty asset blocks.

## 2. Failing test

- [ ] Add the smallest test in the matching `tests/unit/` (or `tests/integration/` if it only shows end to end) folder, following the Testing section of `AGENTS.md`.
- [ ] Run it: `uv run python -m pytest <path>::<test> -x -q`. It must fail for the reason in the bug report. If it passes, the reproduction is wrong; go back to step 1.

## 3. Fix

- [ ] Fix the root cause in the layer where it goes wrong, with a focused diff and no drive-by refactors.
- [ ] If the fix needs a new function, class, or public API change, ask the user first.
- [ ] Never loosen an existing assertion, tolerance, or tool config to get green.

## 4. Verify

- [ ] The new test passes and the old ones still do.
- [ ] Follow the `verify` playbook.
- [ ] Add a `CHANGELOG.md` entry if the bug was user-visible.
