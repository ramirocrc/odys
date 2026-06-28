---
icon: lucide/cpu
---

# Solvers

Odys supports multiple optimization solvers: HiGHS (default), Gurobi, CPLEX, and SCIP. This page covers installation, selection, and configuration.

## Supported solvers

| Solver | Package             | License           |
| ------ | ------------------- | ----------------- |
| HiGHS  | Included by default | Open-source (MIT) |
| Gurobi | `gurobipy`          | Commercial        |
| CPLEX  | `cplex`             | Commercial        |
| SCIP   | `pyscipopt`         | Open-source (ZIB) |

HiGHS is bundled as a core dependency, so it's always available. The other solvers require installing optional extras.

## Installation

Install commercial solvers via pip extras:

=== "pip"

    ```console
    pip install odys[gurobi]
    pip install odys[cplex]
    pip install odys[scip]
    pip install odys[gurobi,cplex,scip]  # all solvers
    ```

=== "uv"

    ```console
    uv add odys[gurobi]
    uv add odys[cplex]
    uv add odys[scip]
    uv add odys[gurobi,cplex,scip]  # all solvers
    ```

You only need to install the solvers you plan to use. If you request a solver that isn't installed, Odys raises `OdysSolverError` with a list of available solvers.

## Selecting a solver

Pass a `SolverConfig` to `EnergySystem.optimize()`:

```python
from odys import EnergySystem, SolverConfig, SolverName

result = energy_system.optimize(
    SolverConfig(solver_name=SolverName.GUROBI)
)
```

When you don't pass a `SolverConfig`, Odys uses HiGHS with default settings.

## Configuration options

`SolverConfig` accepts these common options, automatically translated to each solver's native parameter names:

| Option           | Type                       | Default | Description                          |
| ---------------- | -------------------------- | ------- | ------------------------------------ |
| `solver_name`    | `SolverName`               | `HIGHS` | Which solver backend to use          |
| `time_limit`     | `float \| None`            | `None`  | Max solve time in seconds            |
| `mip_rel_gap`    | `float \| None`            | `None`  | Relative MIP gap tolerance (0 to 1)  |
| `presolve`       | `bool`                     | `False` | Enable solver presolve               |
| `threads`        | `int \| None`              | `None`  | Number of solver threads             |
| `log_output`     | `bool`                     | `False` | Display solver output logs           |
| `solver_options` | `dict[str, Any] \| None`   | `None`  | Raw solver-specific options          |

Example with common options:

```python
from odys import SolverConfig, SolverName

result = energy_system.optimize(
    SolverConfig(
        solver_name=SolverName.GUROBI,
        time_limit=60.0,
        mip_rel_gap=0.01,
        threads=4,
        log_output=True,
    )
)
```

## Solver-specific options

For parameters not covered by the common options, use the `solver_options` dict to pass raw solver-native parameters:

```python
result = energy_system.optimize(
    SolverConfig(
        solver_name=SolverName.GUROBI,
        solver_options={"Method": 2, "Cuts": 2},
    )
)
```

Values in `solver_options` override the translated common options if there's a conflict.

### Native parameter names

Each solver uses different names for the same option. Here's how the common options map:

| Common option   | HiGHS            | Gurobi              | CPLEX                             | SCIP                    |
| --------------- | ---------------- | ------------------- | --------------------------------- | ----------------------- |
| `time_limit`    | `time_limit`     | `TimeLimit`         | `timelimit`                       | `limits/time`           |
| `mip_rel_gap`   | `mip_rel_gap`    | `MIPGap`            | `mip.tolerances.mipgap`           | `limits/gap`            |
| `threads`       | `threads`        | `Threads`           | `threads`                         | `parallel/maxnthreads`  |
| `presolve`      | `presolve`       | `Presolve`          | `preprocessing.presolve`          | `presolving/maxrounds`  |
| `log_output`    | `output_flag`    | `OutputFlag`        | `mip.display` + `output.clonelog` | `display/verblevel`     |

You can use either the common option names or the native names in `solver_options`. When in doubt, check the solver's official documentation for the exact parameter names and valid values.

## Availability check

Before solving, Odys verifies the requested solver is installed. If it's not available, you'll get an `OdysSolverError` listing all installed solvers:

```python
from odys import SolverConfig, SolverName
from odys.exceptions import OdysSolverError

try:
    result = energy_system.optimize(
        SolverConfig(solver_name=SolverName.GUROBI)
    )
except OdysSolverError as e:
    print(f"Solver not available: {e}")
```

This makes it safe to write code that tries multiple solvers or gracefully falls back to HiGHS.

## Next steps

Ready to handle uncertainty? See [Stochastic Optimization](stochastic.md) to optimize across multiple possible futures.
