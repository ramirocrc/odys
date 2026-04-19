# Solvers API

The solvers module contains solver configuration and dispatch for energy system optimization.

## Supported Solvers

Odys supports the following solvers:

| Solver | Package | Installation | License |
|--------|---------|--------------|---------|
| HiGHS | `highspy` | Included by default | Open-source (MIT) |
| Gurobi | `gurobipy` | `uv add odys[gurobi]` | Commercial |
| CPLEX | `cplex` | `uv add odys[cplex]` | Commercial |
| SCIP | `pyscipopt` | `uv add odys[scip]` | Open-source (ZIB) |

## Configuration

To use a different solver, specify it in `SolverConfig`:

```python
from odys import SolverConfig, SolverName

config = SolverConfig(
    solver_name=SolverName.GUROBI,
    time_limit=300,
    presolve=True,
)
```

Then pass it to `EnergySystem.optimize(solver_config=config)`.

## Solver

::: odys.solvers.solver

## Solver Configuration

::: odys.solvers.solver_config

## Option Translators

::: odys.solvers.config_translators
