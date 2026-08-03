# Odys

[![CI](https://img.shields.io/github/actions/workflow/status/ramirocrc/odys/main.yml?branch=main)](https://github.com/ramirocrc/odys/actions/workflows/main.yml?query=branch%3Amain)
[![Coverage](https://codecov.io/gh/ramirocrc/odys/branch/main/graph/badge.svg)](https://codecov.io/gh/ramirocrc/odys)
[![Python versions](https://img.shields.io/pypi/pyversions/odys?color=green)](https://pypi.org/project/odys/)
[![PyPI](https://img.shields.io/pypi/v/odys)](https://pypi.org/project/odys/)
[![License](https://img.shields.io/github/license/ramirocrc/odys)](https://github.com/ramirocrc/odys/blob/main/LICENSE)

Optimize energy portfolios under uncertainty.

**[Documentation](https://ramirocrc.github.io/odys/)** | **[Examples](https://ramirocrc.github.io/odys/examples/)**

## Installation

```console
pip install odys
```

Requires Python 3.11+. For commercial solvers (Gurobi, CPLEX, SCIP), see the [solver docs](https://ramirocrc.github.io/odys/user_guide/solvers/).

## Quick example

Define your assets, describe the scenario, and call `.optimize()`:

```python
from datetime import timedelta

from odys import AssetPortfolio, EnergySystem, FixedLoad, Generator, Scenario

generator = Generator(name="gen", nominal_power=100.0, variable_cost=50.0)
load = FixedLoad(name="demand")

portfolio = AssetPortfolio([generator, load])

energy_system = EnergySystem(
    portfolio=portfolio,
    scenarios=Scenario(fixed_load_profiles={"demand": [60, 90, 40, 70]}),
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
Name: generator_power, dtype: float64
```

See the [documentation](https://ramirocrc.github.io/odys/) for the full workflow, or check the [examples](https://ramirocrc.github.io/odys/examples/) for complete worked scenarios.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup and guidelines.

## License

[MIT](LICENSE)
