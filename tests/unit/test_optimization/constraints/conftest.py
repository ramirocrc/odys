from datetime import timedelta

import pytest
from linopy import Model

from odys.domain.entities.generator import Generator
from odys.domain.entities.load import Load
from odys.energy_system import EnergySystem
from odys.optimization.model.model_builder import build_model
from odys.optimization.parameters.parameters import EnergySystemParameters


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
def energy_system_parameters(
    energy_system_sample: EnergySystem,
) -> EnergySystemParameters:
    """Build energy system parameters from a EnergySystem fixture."""
    return energy_system_sample.build_parameters()


@pytest.fixture
def linopy_model(energy_system_parameters: EnergySystemParameters) -> Model:
    """Build a linopy model from energy system parameters.

    Each test module must define its own `energy_system_sample` fixture.
    """
    return build_model(energy_system_parameters).linopy_model
