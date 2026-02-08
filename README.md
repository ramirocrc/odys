# odys

[![CI](https://img.shields.io/github/actions/workflow/status/ramirocrc/odys/main.yml?branch=main)](https://github.com/ramirocrc/odys/actions/workflows/main.yml?query=branch%3Amain)
[![Coverage](https://codecov.io/gh/ramirocrc/odys/branch/main/graph/badge.svg)](https://codecov.io/gh/ramirocrc/odys)
[![Python versions](https://img.shields.io/pypi/pyversions/odys?color=green)](https://pypi.org/project/odys/)
[![PyPI](https://img.shields.io/pypi/v/odys)](https://pypi.org/project/odys/)
[![Commit activity](https://img.shields.io/github/commit-activity/m/ramirocrc/odys)](https://img.shields.io/github/commit-activity/m/ramirocrc/odys)
[![License](https://img.shields.io/github/license/ramirocrc/odys)](https://img.shields.io/github/license/ramirocrc/odys)

---

- **Github repository**: <https://github.com/ramirocrc/odys/>
- **Documentation** <https://ramirocrc.github.io/odys/>

---

Odys is a Python package for optimizing multi-asset energy portfolios across multiple electricity markets using stochastic optimization.

**Odys** is powered by <a href="https://pydantic-docs.helpmanual.io/" class="external-link" target="_blank">Pydantic</a>, <a href="https://linopy.readthedocs.io/" class="external-link" target="_blank">linopy</a>, and <a href="https://ergo-code.github.io/HiGHS/" class="external-link" target="_blank">HiGHS</a> .

The key features are:

- **Intuitive to write**: Great editor support. <abbr title="also known as auto-complete, autocompletion, IntelliSense">Completion</abbr> everywhere. Less time debugging. Designed to be easy to use and learn. Less time reading docs.
- **Simple API**: Define your energy system (generators, batteries, loads, markets) and call .optimize(). The mathematical model is built and solved for you under the hood.
- **Pydantic-powered validation**: All models are built on Pydantic with strict typing and validators, catching configuration errors early.
- **Stochastic optimization**: Optimize across multiple probabilistic scenarios with different prices, capacities, and load profiles to make decisions under uncertainty.

## Requirements

A recent and currently supported <a href="https://www.python.org/downloads/" class="external-link" target="_blank">version of Python</a>.

As **Odys** is based on **Pydantic**, **linopy**, and **HiGHS**, it requires them. They will be automatically installed when you install odys.

## Installation

pip:

```console
pip install odys
```

uv:

```console
uv add odys
```

## Example

A generator and a battery working together to meet a fixed load over 4 hourly timesteps:

```python
from datetime import timedelta

from odys.energy_system import EnergySystem
from odys.energy_system_models.assets.generator import PowerGenerator
from odys.energy_system_models.assets.load import Load
from odys.energy_system_models.assets.portfolio import AssetPortfolio
from odys.energy_system_models.assets.storage import Battery
from odys.energy_system_models.scenarios import Scenario

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
    soc_start=25.0,
    soc_end=25.0,
)

load = Load(name="demand")

portfolio = AssetPortfolio()
portfolio.add_asset(generator)
portfolio.add_asset(battery)
portfolio.add_asset(load)

energy_system = EnergySystem(
    portfolio=portfolio,
    scenarios=Scenario(
        load_profiles={"demand": [60, 90, 40, 70]},
    ),
    timestep=timedelta(hours=1),
    number_of_steps=4,
    power_unit="MW",
)

result = energy_system.optimize()
```

## Contributing

For guidance on setting up a development environment and how to make a contribution to odys, see
[Contributing to odys](https://github.com/ramirocrc/odys/blob/main/CONTRIBUTING.md).
