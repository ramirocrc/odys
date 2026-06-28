# Odys

[![CI](https://img.shields.io/github/actions/workflow/status/ramirocrc/odys/main.yml?branch=main)](https://github.com/ramirocrc/odys/actions/workflows/main.yml?query=branch%3Amain)
[![Coverage](https://codecov.io/gh/ramirocrc/odys/branch/main/graph/badge.svg)](https://codecov.io/gh/ramirocrc/odys)
[![Python versions](https://img.shields.io/pypi/pyversions/odys?color=green)](https://pypi.org/project/odys/)
[![PyPI](https://img.shields.io/pypi/v/odys)](https://pypi.org/project/odys/)
[![License](https://img.shields.io/github/license/ramirocrc/odys)](https://github.com/ramirocrc/odys/blob/main/LICENSE)

Optimize energy portfolios under uncertainty.

## Features

- **Optimization under uncertainty**: Stochastic optimization is the default, not an afterthought. Multi-asset, multi-market from day one with built-in CVaR risk management.
- **Multi-solver support**: Swap between HiGHS (default), Gurobi, CPLEX, or SCIP with a single configuration change.
- **Simple API**: Define your assets, describe the uncertainty through scenarios, and call `.optimize()`. No boilerplate, no configuration files.
- **Transparent math**: Every constraint and objective term is documented with equations. You know exactly what the solver sees.

## Why Odys?

In energy systems, deterministic optimization is no longer enough. You need to account for multiple possible futures simultaneously, maximizing expected profit while managing risk.

Odys makes stochastic optimization for energy portfolios as straightforward as possible. Define your assets, describe the uncertainty through scenarios, and let the solver find the optimal dispatch across all possible outcomes.

Whether you're a student learning energy optimization, a researcher prototyping new models, or building decision support tools for industry, Odys lets you focus on the problem instead of the math.

## Installation

pip:

```console
pip install odys
```

uv:

```console
uv add odys
```

Odys requires a recent and currently supported [version of Python](https://www.python.org/downloads/). If you use a commercial solver, install the matching extra as well. See [Solvers](https://ramirocrc.github.io/odys/user_guide/solvers/) for details.

## Quick example

Suppose you have a generator and a fixed demand over 4 hours. How much should the generator produce at each timestep?

First, create a generator with a variable cost and a load representing the demand:

```python
from datetime import timedelta

from odys import AssetPortfolio, EnergySystem, Generator, Load, Scenario

generator = Generator(name="gen", nominal_power=100.0, variable_cost=50.0)
load = Load(name="demand")
```

Wire them into a portfolio and tell the `EnergySystem` what demand looks like over time:

```python
portfolio = AssetPortfolio([generator, load])

energy_system = EnergySystem(
    portfolio=portfolio,
    scenarios=Scenario(load_profiles={"demand": [60, 90, 40, 70]}),
    timestep=timedelta(hours=1),
    number_of_steps=4,
)
```

Call `.optimize()` and look at the results:

```python
result = energy_system.optimize()
print(result.generators.power)
```

The generator meets demand at every timestep:

```
time  generator
0     gen          60.0
1     gen          90.0
2     gen          40.0
3     gen          70.0
Name: generator_power, dtype: float64
```

Add a second generator with a different cost, and the solver will use the cheaper one first and only call on the expensive one when necessary.

See the [documentation](https://ramirocrc.github.io/odys/user_guide/energy_system/) for the full workflow, or check the [examples](https://ramirocrc.github.io/odys/examples/) for complete worked scenarios.

## Dependencies

- [Pydantic](https://docs.pydantic.dev/) — Data validation and settings management
- [linopy](https://linopy.readthedocs.io/) — Linear optimization modeling
- [HiGHS](https://ergo-code.github.io/HiGHS/) — High-performance optimization solver
- [pandas](https://pandas.pydata.org/) — Data analysis and manipulation
- [xarray](https://docs.xarray.dev/) — Multi-dimensional arrays

All dependencies are installed automatically when you install odys.

## Contributing

For guidance on setting up a development environment and how to make a contribution to odys, see [Contributing to odys](https://github.com/ramirocrc/odys/blob/main/CONTRIBUTING.md).

## License

Odys is licensed under the [MIT License](https://github.com/ramirocrc/odys/blob/main/LICENSE).
