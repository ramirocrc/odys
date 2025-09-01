import logging
from datetime import timedelta

import pytest

from optimes._math_model.model_builder import EnergyAlgebraicModelBuilder
from optimes.energy_system_models.assets.generator import PowerGenerator
from optimes.energy_system_models.assets.portfolio import AssetPortfolio
from optimes.energy_system_models.assets.storage import Battery
from optimes.energy_system_models.units import PowerUnit
from optimes.energy_system_models.validated_energy_system import ValidatedEnergySystem

logger = logging.getLogger(__name__)


@pytest.fixture
def asset_portfolio_sample() -> AssetPortfolio:
    portfolio = AssetPortfolio()
    portfolio.add_asset(
        PowerGenerator(
            name="gen1",
            nominal_power=100.0,
            variable_cost=20.0,
        ),
    )
    portfolio.add_asset(
        PowerGenerator(
            name="gen2",
            nominal_power=150.0,
            variable_cost=25.0,
        ),
    )
    portfolio.add_asset(
        Battery(
            name="battery1",
            max_power=200.0,
            capacity=100.0,
            efficiency_charging=1,
            efficiency_discharging=1,
            soc_start=100.0,
            soc_end=50.0,
        ),
    )
    return portfolio


@pytest.fixture
def energy_system_sample(asset_portfolio_sample: AssetPortfolio) -> ValidatedEnergySystem:
    return ValidatedEnergySystem(
        portfolio=asset_portfolio_sample,
        demand_profile=[150, 200, 150],
        timestep=timedelta(hours=1),
        power_unit=PowerUnit.MegaWatt,
    )


def test_model_build_components(energy_system_sample: ValidatedEnergySystem) -> None:
    model_builder = EnergyAlgebraicModelBuilder(energy_system_sample)
    linopy_model = model_builder.build()

    # Variables
    assert "generator_power" in linopy_model.variables
    assert "battery_power_in" in linopy_model.variables
    assert "battery_power_out" in linopy_model.variables
    assert "battery_soc" in linopy_model.variables
    assert "battery_charge_mode" in linopy_model.variables

    # Constraints
    assert "power_balance_constraint" in linopy_model.constraints
    assert "generator_max_power_constraint" in linopy_model.constraints
    assert "battery_max_charge_constraint" in linopy_model.constraints
    assert "battery_max_discharge_constraint" in linopy_model.constraints
    assert "battery_soc_dynamics_constraint" in linopy_model.constraints
    assert "battery_soc_bounds_constraint" in linopy_model.constraints
    assert "battery_soc_end_constraint" in linopy_model.constraints
    assert "battery_soc_start_constraint" in linopy_model.constraints

    # Objective
    assert linopy_model.objective is not None


def test_model_already_built(energy_system_sample: ValidatedEnergySystem) -> None:
    model_builder = EnergyAlgebraicModelBuilder(energy_system_sample)
    model_builder.build()
    with pytest.raises(AttributeError, match="Model has already been built."):
        model_builder.build()


def test_only_generators() -> None:
    pass


def test_only_batteries() -> None:
    pass
