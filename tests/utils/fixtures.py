from datetime import timedelta

import linopy
import pytest

from optimes._math_model.model_builder import EnergyAlgebraicModelBuilder
from optimes.energy_system_models.assets.generator import PowerGenerator
from optimes.energy_system_models.assets.portfolio import AssetPortfolio
from optimes.energy_system_models.assets.storage import Battery
from optimes.energy_system_models.units import PowerUnit
from optimes.energy_system_models.validated_energy_system import ValidatedEnergySystem


@pytest.fixture
def generator1() -> PowerGenerator:
    return PowerGenerator(
        name="gen1",
        nominal_power=100.0,
        variable_cost=20.0,
    )


@pytest.fixture
def generator2() -> PowerGenerator:
    return PowerGenerator(
        name="gen2",
        nominal_power=150.0,
        variable_cost=25.0,
    )


@pytest.fixture
def battery1() -> Battery:
    return Battery(
        name="batt1",
        max_power=200.0,
        capacity=100.0,
        efficiency_charging=0.9,
        efficiency_discharging=0.8,
        soc_start=25.0,
        soc_end=50.0,
    )


@pytest.fixture
def asset_portfolio_sample(
    generator1: PowerGenerator,
    generator2: PowerGenerator,
    battery1: Battery,
) -> AssetPortfolio:
    portfolio = AssetPortfolio()
    portfolio.add_asset(generator1)
    portfolio.add_asset(generator2)
    portfolio.add_asset(battery1)
    return portfolio


@pytest.fixture
def demand_profile_sample() -> list[float]:
    return [150, 200, 150]


@pytest.fixture
def time_index(demand_profile_sample: list[float]) -> list[int]:
    return list(range(len(demand_profile_sample)))


@pytest.fixture
def energy_system_sample(
    asset_portfolio_sample: AssetPortfolio,
    demand_profile_sample: list[float],
) -> ValidatedEnergySystem:
    return ValidatedEnergySystem(
        portfolio=asset_portfolio_sample,
        demand_profile=demand_profile_sample,
        timestep=timedelta(hours=1),
        power_unit=PowerUnit.MegaWatt,
    )


@pytest.fixture
def linopy_model(energy_system_sample: ValidatedEnergySystem) -> linopy.Model:
    model_builder = EnergyAlgebraicModelBuilder(energy_system_sample)
    return model_builder.build()


@pytest.fixture(params=["generator1", "generator2"])
def generator(request) -> PowerGenerator:  # noqa: ANN001
    return request.getfixturevalue(request.param)
