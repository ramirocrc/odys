from datetime import timedelta

import pytest
from linopy import Model

from odys.energy_system_models.assets.generator import Generator
from odys.energy_system_models.assets.load import Load
from odys.energy_system_models.units import PowerUnit
from odys.energy_system_models.validated_energy_system import ValidatedEnergySystem
from odys.math_model.model_builder import EnergyAlgebraicModelBuilder
from odys.math_model.model_components.parameters.parameters import EnergySystemParameters
from odys.math_model.parameters_builder import build_parameters


@pytest.fixture
def generator1() -> Generator:
    return Generator(
        name="gen1",
        nominal_power=100.0,
        variable_cost=20.0,
    )


@pytest.fixture
def generator2() -> Generator:
    return Generator(
        name="gen2",
        nominal_power=150.0,
        variable_cost=25.0,
    )


@pytest.fixture
def load1() -> Load:
    return Load(name="load1")


@pytest.fixture
def demand_profile_sample() -> list[float]:
    return [150, 200, 150]


@pytest.fixture
def time_index(demand_profile_sample: list[float]) -> list[int]:
    return list(range(len(demand_profile_sample)))


@pytest.fixture
def one_hour_timestep() -> timedelta:
    return timedelta(hours=1)


@pytest.fixture
def megawatt_unit() -> PowerUnit:
    return PowerUnit.MegaWatt


@pytest.fixture
def energy_system_parameters(
    energy_system_sample: ValidatedEnergySystem,
) -> EnergySystemParameters:
    """Build energy system parameters from a ValidatedEnergySystem fixture."""
    return build_parameters(energy_system_sample)


@pytest.fixture
def linopy_model(energy_system_parameters: EnergySystemParameters) -> Model:
    """Build a linopy model from energy system parameters.

    Each test module must define its own `energy_system_sample` fixture.
    """
    model_builder = EnergyAlgebraicModelBuilder(energy_system_parameters=energy_system_parameters)
    energy_milp_model = model_builder.build()
    return energy_milp_model.linopy_model
