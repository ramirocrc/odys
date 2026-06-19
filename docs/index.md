---
icon: lucide/home
---

<div class="mdx-hero">
  <h1>Odys</h1>
  <p class="mdx-hero__lead">
    Python framework for optimizing multi-asset energy portfolios across multiple electricity markets using stochastic optimization.
  </p>
  <div class="mdx-hero__badges">
    <a href="https://github.com/ramirocrc/odys/actions/workflows/main.yml?query=branch%3Amain">
      <img alt="CI" src="https://img.shields.io/github/actions/workflow/status/ramirocrc/odys/main.yml?branch=main">
    </a>
    <a href="https://codecov.io/gh/ramirocrc/odys">
      <img alt="Coverage" src="https://codecov.io/gh/ramirocrc/odys/branch/main/graph/badge.svg">
    </a>
    <a href="https://pypi.org/project/odys/">
      <img alt="Python versions" src="https://img.shields.io/pypi/pyversions/odys?color=green">
    </a>
    <a href="https://pypi.org/project/odys/">
      <img alt="PyPI" src="https://img.shields.io/pypi/v/odys">
    </a>
    <a href="https://github.com/ramirocrc/odys/blob/main/LICENSE">
      <img alt="License" src="https://img.shields.io/github/license/ramirocrc/odys">
    </a>
  </div>
  <div class="mdx-hero__buttons">
    <a href="user_guide/energy_system.md" class="md-button md-button--primary">Get started</a>
    <a href="https://github.com/ramirocrc/odys" class="md-button">View on GitHub</a>
  </div>
</div>

<div class="mdx-features grid cards" markdown>

-   :material-lightning-bolt: __Simple API__

    Define your assets (generator, storage, load) and call `.optimize()`. The mathematical model is built and solved for you under the hood.

-   :material-chart-bar: __Stochastic Optimization__

    Optimize across multiple probabilistic scenarios with different prices, capacities, and load profiles to make decisions under uncertainty.

-   :material-shield-check: __Pydantic-powered validation__

    All models use Pydantic with strict typing and validators — configuration errors get caught early.

-   :material-cube-outline: __Multi-solver support__

    Swap between HiGHS (default), Gurobi, CPLEX, or SCIP with a single configuration change.

</div>

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

Odys requires a recent and currently supported [version of Python](https://www.python.org/downloads/). If you use a commercial solver, install the matching extra as well.

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

portfolio = AssetPortfolio()
portfolio.add_asset(generator)
portfolio.add_asset(storage)
portfolio.add_asset(load)

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

- [Pydantic](https://docs.pydantic.dev/) — Data validation and settings management
- [linopy](https://linopy.readthedocs.io/) — Linear optimization modeling
- [HiGHS](https://ergo-code.github.io/HiGHS/) — High-performance optimization solver
- [pandas](https://pandas.pydata.org/) — Data analysis and manipulation
- [xarray](https://docs.xarray.dev/) — Multi-dimensional arrays

All dependencies are installed automatically when you install odys.

## License

Odys is licensed under the [MIT License](https://github.com/ramirocrc/odys/blob/main/LICENSE).
