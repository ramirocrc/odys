---
icon: lucide/home
---

<div class="mdx-hero">
  <h1>Odys</h1>
  <p class="mdx-hero__lead">
    Optimize energy portfolios under uncertainty.
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

-   :material-chart-bar: **Optimization under uncertainty**

    Stochastic optimization is the default, not an afterthought. Multi-asset, multi-market from day one with built-in CVaR risk management.

-   :material-cube-outline: **Multi-solver support**

    Swap between HiGHS (default), Gurobi, CPLEX, or SCIP with a single configuration change.

-   :material-lightning-bolt: **Simple API**

    Define your assets, describe the uncertainty through scenarios, and call `.optimize()`. No boilerplate, no configuration files.

-   :material-math-log: **Transparent math**

    Every constraint and objective term is documented with equations. You know exactly what the solver sees.

</div>

## Why Odys?


In energy systems, deterministic optimization is no longer enough. You need to account for multiple possible futures simultaneously, maximizing expected profit while managing risk.

Odys makes stochastic optimization for energy portfolios as straightforward as possible. Define your assets, describe the uncertainty through scenarios, and let the solver find the optimal dispatch across all possible outcomes.

Whether you're a student learning energy optimization, a researcher prototyping new models, or building decision support tools for industry, Odys lets you focus on the problem instead of the math.
## Installation

=== "pip"

    ```console
    pip install odys
    ```

=== "uv"

    ```console
    uv add odys
    ```

Odys requires a recent and currently supported [version of Python](https://www.python.org/downloads/). If you use a commercial solver, install the matching extra as well. See [Solvers](user_guide/solvers.md) for details.

## Quick example

Suppose you have a generator and a fixed demand over 4 hours. How much should the generator produce at each timestep?

Let's walk through this. First, we create a generator with a variable cost and a load representing the demand:

```python
from datetime import timedelta

from odys import AssetPortfolio, EnergySystem, Generator, Load, Scenario

generator = Generator(name="gen", nominal_power=100.0, variable_cost=50.0)
load = Load(name="demand")
```

Now we wire them into a portfolio and tell the `EnergySystem` what demand looks like over time:

```python
portfolio = AssetPortfolio([generator, load])

energy_system = EnergySystem(
    portfolio=portfolio,
    scenarios=Scenario(load_profiles={"demand": [60, 90, 40, 70]}),
    timestep=timedelta(hours=1),
    number_of_steps=4,
)
```

Finally, we call `.optimize()` and look at the results:

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

Notice how the generator output matches demand exactly at every timestep. There's only one source of power, so the optimizer has no choice but to dispatch it to cover the load. Add a second generator with a different cost, and the story gets a lot more interesting -- the solver will use the cheaper one first and only call on the expensive one when necessary.

See [EnergySystem](user_guide/energy_system.md) to understand the full workflow, or jump to the [Examples](examples/index.md) for complete worked scenarios.

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
