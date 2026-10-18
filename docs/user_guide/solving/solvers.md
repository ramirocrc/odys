---
icon: lucide/cpu
---

# Solvers

`.optimize()` solves with HiGHS by default, and the models in this guide solve in milliseconds. Real models get bigger: a large fleet, a year of quarter-hours, many scenarios. When a run gets slow, this page shows how to cap its time and accept a small gap, fix a seed for reproducible runs, or switch to a commercial solver.

Before tuning the solver, look at the model: its binaries grow with the number of steps times the number of scenarios. See [Horizon and problem size](../model/time_and_units.md#horizon-and-problem-size), and the [binaries table](../../formulation/index.md#problem-class-and-size) of the Mathematical Formulation.

## Supported solvers

| Solver | Package             | License           |
| ------ | ------------------- | ----------------- |
| HiGHS  | Included by default | Open-source (MIT) |
| Gurobi | `gurobipy`          | Commercial        |
| CPLEX  | `cplex`             | Commercial        |
| SCIP   | `pyscipopt`         | Open-source (ZIB) |

HiGHS is bundled as a core dependency, so it's always available. The other solvers require installing optional extras, and Gurobi and CPLEX also need a license.

## Installation

Install the optional solvers as extras:

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

The snippets on this page solve the first system of [Your first model](../model/first_model.md#basic-usage):

??? example "The system"

    ```python
    from datetime import timedelta

    from odys import AssetPortfolio, EnergySystem, FixedLoad, Generator, LoadProfile, Scenario

    ccgt = Generator(name="ccgt", nominal_power=100.0, variable_cost=50.0)
    factory = FixedLoad(name="factory")

    energy_system = EnergySystem(
        portfolio=AssetPortfolio([ccgt, factory]),
        scenarios=Scenario(profiles=(LoadProfile(load=factory, values=[60, 90, 40, 70]),)),
        timestep=timedelta(hours=1),
        number_of_steps=4,
    )
    ```

Pass a `SolverConfig` to `EnergySystem.optimize()`:

```python
from odys import SolverConfig, SolverName

result = energy_system.optimize(SolverConfig(solver_name=SolverName.HIGHS))
```

When you don't pass a `SolverConfig`, Odys uses HiGHS with default settings. To use another solver, install it and change `solver_name`, for example `SolverName.GUROBI`.

## Configuration options

`SolverConfig` accepts these common options, automatically translated to each solver's native parameter names:

| Option           | Type                       | Default | Description                          |
| ---------------- | -------------------------- | ------- | ------------------------------------ |
| `solver_name`    | `SolverName`               | `HIGHS` | Which solver backend to use          |
| `time_limit`     | `float \| None`            | `None`  | Max solve time in seconds            |
| `mip_rel_gap`    | `float \| None`            | `None`  | Relative MIP gap tolerance (0 to 1)  |
| `presolve`       | `bool \| None`             | `None`  | Turn presolve on or off; `None` keeps the solver's default |
| `threads`        | `int \| None`              | `None`  | Number of solver threads             |
| `log_output`     | `bool`                     | `False` | Display solver output logs           |
| `solver_options` | `dict[str, Any] \| None`   | `None`  | Raw solver-specific options          |

Options left at `None` keep each solver's own default, so presolve runs unless you set `presolve=False`. For example, to stop after a minute or within 1 % of the best possible plan, whichever comes first:

```python
result = energy_system.optimize(
    SolverConfig(
        solver_name=SolverName.HIGHS,
        time_limit=60.0,
        mip_rel_gap=0.01,
        threads=4,
    )
)
```

A run that stops on its time limit or its gap may return a plan that's feasible but not proven optimal. `result.termination_condition` says why it stopped; see [Solver status](results.md#solver-status).

## Solver-specific options

For parameters not covered by the common options, use the `solver_options` dict to pass raw solver-native parameters. For example, HiGHS's random seed and MIP feasibility tolerance:

```python
result = energy_system.optimize(
    SolverConfig(
        solver_name=SolverName.HIGHS,
        solver_options={"random_seed": 42, "mip_feasibility_tolerance": 1e-7},
    )
)
```

With Gurobi, the same dict takes Gurobi's names, such as `{"Method": 2, "Cuts": 2}`.

`solver_options` is passed to the solver as it is, so it takes the solver's own parameter names, and its values override the translated common options when both set the same parameter.

### Native parameter names

Each solver uses different names for the same option. Here's how the common options map:

| Common option   | HiGHS            | Gurobi              | CPLEX                             | SCIP                    |
| --------------- | ---------------- | ------------------- | --------------------------------- | ----------------------- |
| `time_limit`    | `time_limit`     | `TimeLimit`         | `timelimit`                       | `limits/time`           |
| `mip_rel_gap`   | `mip_rel_gap`    | `MIPGap`            | `mip.tolerances.mipgap`           | `limits/gap`            |
| `threads`       | `threads`        | `Threads`           | `threads`                         | `parallel/maxnthreads`  |
| `presolve`      | `presolve`       | `Presolve`          | `preprocessing.presolve`          | `presolving/maxrounds`  |
| `log_output`    | `output_flag`    | `OutputFlag`        | `mip.display` + `output.clonelog` | `display/verblevel`     |

In `solver_options`, always use the native names: a common name such as `time_limit` only works there for HiGHS, whose names happen to match. Check the solver's own documentation for the exact parameter names and valid values.

## Availability check

Before solving, Odys verifies the requested solver is installed. If it's not available, you'll get an `OdysSolverError` listing all installed solvers:

```python
from odys import OdysSolverError

try:
    result = energy_system.optimize(
        SolverConfig(solver_name=SolverName.GUROBI)
    )
except OdysSolverError as e:
    print(f"Solver not available: {e}")
```

This makes it safe to write code that tries multiple solvers or gracefully falls back to HiGHS.

## Next steps

A run can also fail before the solver starts, because an input breaks a rule. Next, see what odys checks, in [Validation and errors](validation.md).
