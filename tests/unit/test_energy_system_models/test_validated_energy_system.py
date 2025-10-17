"""Tests for the EnergySystem class.

This module contains tests for the EnergySystem class which represents
the complete energy system configuration including asset portfolio,
demand profile, and validation logic.
"""

from datetime import timedelta

import pytest

from optimes.energy_system_models.assets.generator import PowerGenerator
from optimes.energy_system_models.assets.load import Load
from optimes.energy_system_models.assets.portfolio import AssetPortfolio
from optimes.energy_system_models.assets.storage import Battery
from optimes.energy_system_models.scenarios import Scenario
from optimes.energy_system_models.units import PowerUnit
from optimes.energy_system_models.validated_energy_system import ValidatedEnergySystem


@pytest.fixture
def testing_generator() -> PowerGenerator:
    return PowerGenerator(
        name="test_generator",
        nominal_power=100.0,  # 100 MW
        variable_cost=50.0,  # 50 currency/MWh
    )


@pytest.fixture
def testing_battery() -> Battery:
    return Battery(
        name="test_battery",
        capacity=50.0,
        max_power=25.0,
        efficiency_charging=0.9,
        efficiency_discharging=0.9,
        soc_start=25.0,
    )


@pytest.fixture
def testing_load() -> Load:
    return Load(name="test_load")


@pytest.fixture
def testing_portfolio(
    testing_generator: PowerGenerator,
    testing_battery: Battery,
    testing_load: Load,
) -> AssetPortfolio:
    portfolio = AssetPortfolio()
    portfolio.add_asset(testing_generator)
    portfolio.add_asset(testing_battery)
    portfolio.add_asset(testing_load)
    return portfolio


@pytest.fixture
def valid_demand_profile() -> list[float]:
    return [80.0, 120.0, 90.0, 150.0]


@pytest.fixture
def valid_timestep() -> timedelta:
    return timedelta(hours=1)


def test_energy_system_creation_with_valid_inputs(
    testing_portfolio: AssetPortfolio,
    valid_demand_profile: list[float],
    valid_timestep: timedelta,
) -> None:
    """Test that EnergySystem can be created with valid inputs."""
    ValidatedEnergySystem(
        portfolio=testing_portfolio,
        number_of_steps=len(valid_demand_profile),
        timestep=valid_timestep,
        power_unit=PowerUnit.MegaWatt,
        scenarios=Scenario(
            available_capacity_profiles={},
            load_profiles={"test_load": valid_demand_profile},
        ),
    )


def test_validation_of_capacity_profile_lengths(
    testing_portfolio: AssetPortfolio,
    valid_demand_profile: list[float],
    valid_timestep: timedelta,
) -> None:
    """Test validation that available capacity profiles match demand profile length."""
    # Valid capacity profile with matching length
    valid_capacity_profiles = {
        "test_generator": [90.0, 100.0, 95.0, 100.0],
    }

    energy_system = ValidatedEnergySystem(
        portfolio=testing_portfolio,
        number_of_steps=len(valid_demand_profile),
        timestep=valid_timestep,
        scenarios=Scenario(
            available_capacity_profiles=valid_capacity_profiles,
            load_profiles={"test_load": valid_demand_profile},
        ),
        power_unit=PowerUnit.MegaWatt,
    )

    # Note: energy_system.available_capacity_profiles is now an xr.DataArray, not a dict
    assert energy_system.scenarios is not None  # The scenarios is preserved

    invalid_capacity_profiles = {
        "test_generator": [90.0, 100.0],  # Only 2 values instead of 4
    }

    with pytest.raises(ValueError, match="does not match the number of time steps"):
        ValidatedEnergySystem(
            portfolio=testing_portfolio,
            number_of_steps=len(valid_demand_profile),
            timestep=valid_timestep,
            scenarios=Scenario(
                available_capacity_profiles=invalid_capacity_profiles,
                load_profiles={"test_load": valid_demand_profile},
            ),
            power_unit=PowerUnit.MegaWatt,
        )


def test_validation_that_capacity_profiles_only_for_generators(
    testing_portfolio: AssetPortfolio,
    valid_demand_profile: list[float],
    valid_timestep: timedelta,
) -> None:
    """Test validation that available capacity profiles can only be specified for generators."""
    invalid_capacity_profiles = {
        "test_battery": [25.0, 25.0, 25.0, 25.0],
    }

    with pytest.raises(TypeError, match="Available capacity can only be specified for generators"):
        ValidatedEnergySystem(
            portfolio=testing_portfolio,
            number_of_steps=len(valid_demand_profile),
            timestep=valid_timestep,
            scenarios=Scenario(
                available_capacity_profiles=invalid_capacity_profiles,
                load_profiles={"test_load": valid_demand_profile},
            ),
            power_unit=PowerUnit.MegaWatt,
        )


def test_validation_that_system_can_meet_power_demand(
    testing_portfolio: AssetPortfolio,
    valid_timestep: timedelta,
) -> None:
    """Test validation that the system has enough power capacity to meet peak demand."""

    excessive_demand = [80.0, 200.0, 90.0, 150.0]  # 200 MW exceeds 150 MW capacity

    with pytest.raises(ValueError, match="Infeasible problem"):
        ValidatedEnergySystem(
            portfolio=testing_portfolio,
            number_of_steps=len(excessive_demand),
            timestep=valid_timestep,
            power_unit=PowerUnit.MegaWatt,
            scenarios=Scenario(
                available_capacity_profiles={},
                load_profiles={"test_load": excessive_demand},
            ),
        )
