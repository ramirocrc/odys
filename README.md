<h1>
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/ramirocrc/odys/main/docs/assets/brand/odys-wordmark-on-dark.svg">
    <img alt="Odys" src="https://raw.githubusercontent.com/ramirocrc/odys/main/docs/assets/brand/odys-wordmark-on-light.svg" height="56">
  </picture>
</h1>

[![CI](https://img.shields.io/github/actions/workflow/status/ramirocrc/odys/main.yml?branch=main)](https://github.com/ramirocrc/odys/actions/workflows/main.yml?query=branch%3Amain)
[![Coverage](https://codecov.io/gh/ramirocrc/odys/branch/main/graph/badge.svg)](https://codecov.io/gh/ramirocrc/odys)
[![Python versions](https://img.shields.io/pypi/pyversions/odys?color=green)](https://pypi.org/project/odys/)
[![PyPI](https://img.shields.io/pypi/v/odys)](https://pypi.org/project/odys/)
[![License](https://img.shields.io/github/license/ramirocrc/odys)](https://github.com/ramirocrc/odys/blob/main/LICENSE)

Optimize energy portfolios under uncertainty.

---

**[Documentation](https://ramirocrc.github.io/odys/)**

**[Examples](https://ramirocrc.github.io/odys/examples/)**

---

Odys is a free, open-source Python framework for the short-term operation of energy asset portfolios across electricity markets. Generators, storage, electric vehicles, chargers and loads are scheduled against one or more markets, with uncertainty represented by probability-weighted scenarios.

Features:
- **Stochastic optimization**: maximize expected profit over a set of scenarios, with optional stage-fixed (non-anticipative) market positions and a CVaR risk term.
- **Solver choice**: HiGHS by default; Gurobi, CPLEX and SCIP as optional extras. Models are built with [linopy](https://github.com/PyPSA/linopy).
- **Validated inputs**: assets, profiles and scenarios are Pydantic models, checked before the model is built.
- **Documented formulation**: every variable, constraint and objective term is written out in the documentation.

Scope: Odys models a portfolio on a single bus over a short horizon. It does not model networks, power flow or capacity expansion; for those, see [PyPSA](https://pypsa.org/) or [Calliope](https://calliope.readthedocs.io/).

## Installation

```console
pip install odys
```

Requires Python 3.11+. For commercial solvers (Gurobi, CPLEX, SCIP), see the [solver docs](https://ramirocrc.github.io/odys/user_guide/solving/solvers/).

## Quick example

Define your assets, describe the scenario, and call `.optimize()`:

```python
from datetime import timedelta

from odys import AssetPortfolio, LoadProfile, EnergySystem, FixedLoad, Generator, Scenario

generator = Generator(name="gen", nominal_power=100.0, variable_cost=50.0)
load = FixedLoad(name="demand")

portfolio = AssetPortfolio([generator, load])

energy_system = EnergySystem(
    portfolio=portfolio,
    scenarios=Scenario(profiles=(LoadProfile(load=load, values=[60, 90, 40, 70]),)),
    timestep=timedelta(hours=1),
    number_of_steps=4,
)

result = energy_system.optimize()
print(result.generators.power)
```

```
time  generator
0     gen          60.0
1     gen          90.0
2     gen          40.0
3     gen          70.0
Name: power, dtype: float64
```

See the [documentation](https://ramirocrc.github.io/odys/) for the full workflow, or check the [examples](https://ramirocrc.github.io/odys/examples/) for complete worked scenarios.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup and guidelines.

## License

[MIT](LICENSE)
