"""Tests for the EnergySystem class.

This module contains tests for the EnergySystem class which represents
the complete energy system configuration including asset portfolio,
demand profile, and validation logic.
"""

from datetime import timedelta

import pytest

from odys.energy_system_models.assets.generator import PowerGenerator
from odys.energy_system_models.assets.load import Load
from odys.energy_system_models.assets.portfolio import AssetPortfolio
from odys.energy_system_models.assets.storage import Battery
from odys.energy_system_models.markets import EnergyMarket
from odys.energy_system_models.scenarios import Scenario
from odys.energy_system_models.units import PowerUnit
from odys.energy_system_models.validated_energy_system import ValidatedEnergySystem


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


@pytest.fixture
def testing_market() -> EnergyMarket:
    return EnergyMarket(name="test_market", max_trading_volume_per_step=100.0)


@pytest.fixture
def portfolio_without_loads() -> AssetPortfolio:
    portfolio = AssetPortfolio()
    portfolio.add_asset(PowerGenerator(name="gen", nominal_power=100.0, variable_cost=50.0))
    return portfolio


@pytest.fixture
def portfolio_without_generators() -> AssetPortfolio:
    portfolio = AssetPortfolio()
    portfolio.add_asset(
        Battery(
            name="battery",
            capacity=50.0,
            max_power=25.0,
            efficiency_charging=0.9,
            efficiency_discharging=0.9,
            soc_start=25.0,
        ),
    )
    portfolio.add_asset(Load(name="load"))
    return portfolio


@pytest.fixture
def empty_portfolio() -> AssetPortfolio:
    return AssetPortfolio()


def test_load_validation_missing_load_profiles(testing_portfolio: AssetPortfolio) -> None:
    """Test validation when portfolio has loads but scenario has no load profiles."""
    with pytest.raises(ValueError, match=r"Portfolio contains loads.*but scenario.*has no load profiles"):
        ValidatedEnergySystem(
            portfolio=testing_portfolio,
            number_of_steps=4,
            timestep=timedelta(hours=1),
            power_unit=PowerUnit.MegaWatt,
            scenarios=Scenario(
                available_capacity_profiles={},
                load_profiles=None,  # Missing load profiles
            ),
        )


def test_load_validation_missing_specific_load_profile(testing_portfolio: AssetPortfolio) -> None:
    """Test validation when scenario is missing profiles for specific loads."""
    with pytest.raises(ValueError, match=r"Scenario.*is missing load profiles for"):
        ValidatedEnergySystem(
            portfolio=testing_portfolio,
            number_of_steps=4,
            timestep=timedelta(hours=1),
            power_unit=PowerUnit.MegaWatt,
            scenarios=Scenario(
                available_capacity_profiles={},
                load_profiles={},  # Empty dict, missing "test_load"
            ),
        )


def test_load_validation_extra_load_profiles(testing_portfolio: AssetPortfolio) -> None:
    """Test validation when scenario has profiles for loads not in portfolio."""
    with pytest.raises(ValueError, match=r"Scenario.*has load profiles for loads not in portfolio"):
        ValidatedEnergySystem(
            portfolio=testing_portfolio,
            number_of_steps=4,
            timestep=timedelta(hours=1),
            power_unit=PowerUnit.MegaWatt,
            scenarios=Scenario(
                available_capacity_profiles={},
                load_profiles={
                    "test_load": [80.0, 120.0, 90.0, 150.0],
                    "extra_load": [10.0, 20.0, 30.0, 40.0],  # Not in portfolio
                },
            ),
        )


def test_load_validation_no_loads_but_has_profiles(portfolio_without_loads: AssetPortfolio) -> None:
    """Test validation when portfolio has no loads but scenario has load profiles."""
    with pytest.raises(ValueError, match=r"Portfolio contains no loads.*but scenario.*has load profiles"):
        ValidatedEnergySystem(
            portfolio=portfolio_without_loads,
            number_of_steps=4,
            timestep=timedelta(hours=1),
            power_unit=PowerUnit.MegaWatt,
            scenarios=Scenario(
                available_capacity_profiles={},
                load_profiles={"some_load": [80.0, 120.0, 90.0, 150.0]},
            ),
        )


def test_market_validation_missing_market_prices(
    testing_portfolio: AssetPortfolio,
    testing_market: EnergyMarket,
) -> None:
    """Test validation when portfolio has markets but scenario has no market prices."""
    with pytest.raises(ValueError, match=r"Portfolio contains markets.*but scenario.*has no market prices"):
        ValidatedEnergySystem(
            portfolio=testing_portfolio,
            number_of_steps=4,
            timestep=timedelta(hours=1),
            power_unit=PowerUnit.MegaWatt,
            markets=testing_market,
            scenarios=Scenario(
                available_capacity_profiles={},
                load_profiles={"test_load": [80.0, 120.0, 90.0, 150.0]},
                market_prices=None,  # Missing market prices
            ),
        )


def test_market_validation_missing_specific_market_prices(
    testing_portfolio: AssetPortfolio,
    testing_market: EnergyMarket,
) -> None:
    """Test validation when scenario is missing prices for specific markets."""
    with pytest.raises(ValueError, match=r"Scenario.*is missing market prices for"):
        ValidatedEnergySystem(
            portfolio=testing_portfolio,
            number_of_steps=4,
            timestep=timedelta(hours=1),
            power_unit=PowerUnit.MegaWatt,
            markets=testing_market,
            scenarios=Scenario(
                available_capacity_profiles={},
                load_profiles={"test_load": [80.0, 120.0, 90.0, 150.0]},
                market_prices={},  # Empty dict, missing "test_market"
            ),
        )


def test_market_validation_extra_market_prices(testing_portfolio: AssetPortfolio, testing_market: EnergyMarket) -> None:
    """Test validation when scenario has prices for markets not in portfolio."""
    with pytest.raises(ValueError, match=r"Scenario.*has market prices for markets not in portfolio"):
        ValidatedEnergySystem(
            portfolio=testing_portfolio,
            number_of_steps=4,
            timestep=timedelta(hours=1),
            power_unit=PowerUnit.MegaWatt,
            markets=testing_market,
            scenarios=Scenario(
                available_capacity_profiles={},
                load_profiles={"test_load": [80.0, 120.0, 90.0, 150.0]},
                market_prices={
                    "test_market": [10.0, 20.0, 30.0, 40.0],
                    "extra_market": [5.0, 15.0, 25.0, 35.0],  # Not in portfolio
                },
            ),
        )


def test_market_validation_no_markets_but_has_prices(portfolio_without_loads: AssetPortfolio) -> None:
    """Test validation when portfolio has no markets but scenario has market prices."""
    with pytest.raises(ValueError, match=r"Portfolio contains no markets.*but scenario.*has market prices"):
        ValidatedEnergySystem(
            portfolio=portfolio_without_loads,
            number_of_steps=4,
            timestep=timedelta(hours=1),
            power_unit=PowerUnit.MegaWatt,
            scenarios=Scenario(
                available_capacity_profiles={},
                load_profiles=None,
                market_prices={"some_market": [10.0, 20.0, 30.0, 40.0]},
            ),
        )


def test_load_profile_length_validation(testing_portfolio: AssetPortfolio) -> None:
    """Test validation of load profile length mismatch."""
    with pytest.raises(ValueError, match=r"Length of load profile.*does not match the number of time steps"):
        ValidatedEnergySystem(
            portfolio=testing_portfolio,
            number_of_steps=4,
            timestep=timedelta(hours=1),
            power_unit=PowerUnit.MegaWatt,
            scenarios=Scenario(
                available_capacity_profiles={},
                load_profiles={"test_load": [80.0, 120.0]},  # Only 2 values instead of 4
            ),
        )


def test_capacity_profile_value_validation(testing_portfolio: AssetPortfolio) -> None:
    """Test validation of capacity profile values outside valid range."""
    with pytest.raises(ValueError, match=r"Available capacity value.*is invalid"):
        ValidatedEnergySystem(
            portfolio=testing_portfolio,
            number_of_steps=4,
            timestep=timedelta(hours=1),
            power_unit=PowerUnit.MegaWatt,
            scenarios=Scenario(
                available_capacity_profiles={
                    "test_generator": [90.0, 150.0, 95.0, 100.0],  # 150.0 exceeds nominal_power of 100.0
                },
                load_profiles={"test_load": [80.0, 120.0, 90.0, 100.0]},
            ),
        )


def test_empty_load_profiles_validation(portfolio_without_loads: AssetPortfolio) -> None:
    """Test validation when load profiles is empty (should trigger empty load profile error)."""
    with pytest.raises(ValueError, match="Load profile is empty, there is nothing to balance"):
        ValidatedEnergySystem(
            portfolio=portfolio_without_loads,
            number_of_steps=4,
            timestep=timedelta(hours=1),
            power_unit=PowerUnit.MegaWatt,
            scenarios=Scenario(
                available_capacity_profiles={},
                load_profiles=None,
            ),
        )
