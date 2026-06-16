# Odys

[![CI](https://img.shields.io/github/actions/workflow/status/ramirocrc/odys/main.yml?branch=main)](https://github.com/ramirocrc/odys/actions/workflows/main.yml?query=branch%3Amain)
[![Coverage](https://codecov.io/gh/ramirocrc/odys/branch/main/graph/badge.svg)](https://codecov.io/gh/ramirocrc/odys)
[![Python versions](https://img.shields.io/pypi/pyversions/odys?color=green)](https://pypi.org/project/odys/)
[![PyPI](https://img.shields.io/pypi/v/odys)](https://pypi.org/project/odys/)
[![License](https://img.shields.io/github/license/ramirocrc/odys)](https://github.com/ramirocrc/odys/blob/main/LICENSE)

---

**Documentation**: [https://ramirocrc.github.io/odys/](https://ramirocrc.github.io/odys/)

**Source Code**: [https://github.com/ramirocrc/odys/](https://github.com/ramirocrc/odys/)

---

Odys helps you model and optimize multi-asset energy systems across multiple electricity markets.

## Start here

- Read the [User Guide](user_guide/energy_system.md) to learn the core workflow
- Browse [Examples](examples/index.md) to see complete, runnable scenarios
- Use the [API Reference](api/index.md) when you need implementation details

## Overview

Odys is a Python package for optimizing multi-asset energy portfolios across multiple electricity markets using stochastic optimization.

The key features are:

- **Simple API** - Define your energy system (generators, storages, loads, markets) and call `.optimize()`. The mathematical model is built and solved for you under the hood.
- **Pydantic-powered validation** - All models use Pydantic with strict typing and validators, so configuration errors get caught early.
- **Stochastic optimization** - Optimize across multiple probabilistic scenarios with different prices, capacities, and load profiles to make decisions under uncertainty.
- **Great editor support** - Full autocompletion and type checking everywhere, so you spend less time debugging.

## Installation

=== "pip"

    ```console
    pip install odys
    pip install odys[gurobi]   # or cplex, scip
    ```

=== "uv"

    ```console
    uv add odys
    uv add odys[gurobi]   # or cplex, scip
    ```

Odys requires a recent and currently supported [version of Python](https://www.python.org/downloads/).
If you use a commercial solver, install the matching extra as well.

### Supported Solvers

| Solver | Package             | License           |
| ------ | ------------------- | ----------------- |
| HiGHS  | Included by default | Open-source (MIT) |
| Gurobi | `gurobipy`          | Commercial        |
| CPLEX  | `cplex`             | Commercial        |
| SCIP   | `pyscipopt`         | Open-source (ZIB) |

## Quick example

This is the shortest path from model setup to solution.

```python
from datetime import timedelta

from odys import AssetPortfolio, EnergySystem, Generator, Load, Scenario, Storage

# Define assets
generator = Generator(
    name="gen",
    nominal_power=100.0,
    variable_cost=50.0,
)

storage = Storage(
    name="bess",
    capacity=50.0,
    max_power=25.0,
    efficiency_charging=0.95,
    efficiency_discharging=0.95,
    soc_start=0.5,
    soc_end=0.5,
)

load = Load(name="demand")

# Build the portfolio
portfolio = AssetPortfolio()
portfolio.add_asset(generator)
portfolio.add_asset(storage)
portfolio.add_asset(load)

# Set up the energy system
energy_system = EnergySystem(
    portfolio=portfolio,
    scenarios=Scenario(
        load_profiles={"demand": [60, 90, 40, 70]},
    ),
    timestep=timedelta(hours=1),
    number_of_steps=4,
)
result = energy_system.optimize()

print(result.solver_status)
print(result.generators.power)
```

See the [Examples](examples/index.md) page for fuller scenarios.

## Dependencies

Odys depends on a small set of core libraries:

- [Pydantic](https://docs.pydantic.dev/) - Data validation and settings management
- [linopy](https://linopy.readthedocs.io/) - Linear optimization modeling
- [HiGHS](https://ergo-code.github.io/HiGHS/) - High-performance optimization solver (optional: Gurobi, CPLEX, SCIP available via extras)
- [pandas](https://pandas.pydata.org/) - Data analysis and manipulation
- [xarray](https://docs.xarray.dev/) - Multi-dimensional arrays

All dependencies are installed automatically when you install odys.

## License

Odys is licensed under the [MIT License](https://github.com/ramirocrc/odys/blob/main/LICENSE).
