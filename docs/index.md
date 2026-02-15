# Odys

[![CI](https://img.shields.io/github/actions/workflow/status/ramirocrc/odys/main.yml?branch=main)](https://github.com/ramirocrc/odys/actions/workflows/main.yml?query=branch%3Amain)
[![Coverage](https://codecov.io/gh/ramirocrc/odys/branch/main/graph/badge.svg)](https://codecov.io/gh/ramirocrc/odys)
[![Python versions](https://img.shields.io/pypi/pyversions/odys?color=green)](https://pypi.org/project/odys/)
[![PyPI](https://img.shields.io/pypi/v/odys)](https://pypi.org/project/odys/)
[![License](https://img.shields.io/github/license/ramirocrc/odys)](https://img.shields.io/github/license/ramirocrc/odys)

---

**Documentation**: [https://ramirocrc.github.io/odys/](https://ramirocrc.github.io/odys/)

**Source Code**: [https://github.com/ramirocrc/odys/](https://github.com/ramirocrc/odys/)

---

## Overview

Odys is a Python package for optimizing multi-asset energy portfolios across multiple electricity markets using stochastic optimization. It's built on top of [Pydantic](https://docs.pydantic.dev/), [linopy](https://linopy.readthedocs.io/), and [HiGHS](https://ergo-code.github.io/HiGHS/).

The key features are:

- **Simple API** - Define your energy system (generators, batteries, loads, markets) and call `.optimize()`. The mathematical model is built and solved for you under the hood.
- **Pydantic-powered validation** - All models use Pydantic with strict typing and validators, so configuration errors get caught early.
- **Stochastic optimization** - Optimize across multiple probabilistic scenarios with different prices, capacities, and load profiles to make decisions under uncertainty.
- **Great editor support** - Full autocompletion and type checking everywhere, so you spend less time debugging.

## Installation

=== "pip"

    ```console
    pip install odys
    ```

=== "uv"

    ```console
    uv add odys
    ```

Odys requires a recent and currently supported [version of Python](https://www.python.org/downloads/).

## Minimal Example

A generator and a battery working together to meet a fixed load over 4 hourly timesteps.

### Create it

```python
from datetime import timedelta

from odys.energy_system import EnergySystem
from odys.energy_system_models.assets.generator import PowerGenerator
from odys.energy_system_models.assets.load import Load
from odys.energy_system_models.assets.portfolio import AssetPortfolio
from odys.energy_system_models.assets.storage import Battery
from odys.energy_system_models.scenarios import Scenario

# Define assets
generator = PowerGenerator(
    name="gen",
    nominal_power=100.0,
    variable_cost=50.0,
)

battery = Battery(
    name="battery",
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
portfolio.add_asset(battery)
portfolio.add_asset(load)

# Set up the energy system
energy_system = EnergySystem(
    portfolio=portfolio,
    scenarios=Scenario(
        load_profiles={"demand": [60, 90, 40, 70]},
    ),
    timestep=timedelta(hours=1),
    number_of_steps=4,
    power_unit="MW",
)
```

### Run it

```python
result = energy_system.optimize()
```

### Check it

```python
# Solver status
print(result.solver_status)        # "ok"
print(result.termination_condition) # "optimal"

# Generator dispatch
print(result.generators.power)

# Battery behavior
print(result.batteries.net_power)
print(result.batteries.state_of_charge)

# Everything in one DataFrame
print(result.to_dataframe)
```

## Dependencies

Odys is built on top of these great projects:

- [Pydantic](https://docs.pydantic.dev/) - Data validation and settings management
- [linopy](https://linopy.readthedocs.io/) - Linear optimization modeling
- [HiGHS](https://ergo-code.github.io/HiGHS/) - High-performance optimization solver
- [pandas](https://pandas.pydata.org/) - Data analysis and manipulation
- [xarray](https://docs.xarray.dev/) - Multi-dimensional arrays

All dependencies are installed automatically when you install odys.

## License

Odys is licensed under the [MIT License](https://github.com/ramirocrc/odys/blob/main/LICENSE).

## Citation

If you use odys for a scientific publication, we'd appreciate a citation.

**BibTeX**:

```bibtex
@software{odys,
  author  = {Criach, Ramiro},
  title   = {odys},
  version = {0.1.2},
  month   = {12},
  year    = {2024},
  license = {MIT},
  url     = {https://ramirocrc.github.io/odys/},
}
```
