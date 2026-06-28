---
name: Bug Report
about: Report a bug or unexpected behavior
title: "[BUG] "
labels: ["bug"]
assignees: []
---

## Description

A clear and concise description of the bug.

## Steps to Reproduce

Provide a minimal, reproducible example:

```python
from odys import EnergySystem, Generator, Load, Scenario, AssetPortfolio

# Your code here
```

## Expected Behavior

What you expected to happen.

## Actual Behavior

What actually happened. Include any error messages or tracebacks:

```
Paste error output here
```

## Environment

- **Python version**: `python --version`
- **odys version**: `python -c "from importlib.metadata import version; print(version('odys'))"`
- **OS**: [e.g., macOS 14, Ubuntu 22.04, Windows 11]
- **Solver**: [e.g., HiGHS (default), Gurobi, CPLEX, SCIP]

## Additional Context

Add any other context about the problem here (e.g., screenshots, related issues, workarounds you've tried).

## Checklist

- [ ] I have searched existing issues to avoid duplicates
- [ ] I have included a minimal reproducible example
- [ ] I have provided my environment details
