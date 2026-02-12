import logging
from datetime import timedelta

import pytest

from odys._math_model.model_builder import EnergyAlgebraicModelBuilder
from odys.energy_system_models.assets.generator import PowerGenerator
from odys.energy_system_models.assets.load import Load
from odys.energy_system_models.assets.portfolio import AssetPortfolio
from odys.energy_system_models.assets.storage import Battery
from odys.energy_system_models.scenarios import Scenario
from odys.energy_system_models.units import PowerUnit
from odys.energy_system_models.validated_energy_system import ValidatedEnergySystem

logger = logging.getLogger(__name__)


@pytest.fixture
def load1() -> Load:
    return Load(name="load1")


@pytest.fixture
def asset_portfolio_sample(load1: Load) -> AssetPortfolio:
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
            soc_start=1.0,
            soc_end=0.5,
        ),
    )
    portfolio.add_asset(load1)
    return portfolio


@pytest.fixture
def energy_system_sample(asset_portfolio_sample: AssetPortfolio) -> ValidatedEnergySystem:
    demand_profile = [150, 200, 150]
    return ValidatedEnergySystem(
        portfolio=asset_portfolio_sample,
        number_of_steps=len(demand_profile),
        timestep=timedelta(hours=1),
        power_unit=PowerUnit.MegaWatt,
        scenarios=Scenario(
            available_capacity_profiles={},
            load_profiles={"load1": demand_profile},
        ),
    )


def test_model_build_components(energy_system_sample: ValidatedEnergySystem) -> None:
    model_builder = EnergyAlgebraicModelBuilder(
        energy_system_sample.energy_system_parameters,
    )
    energy_milp_model = model_builder.build()
    linopy_model = energy_milp_model.linopy_model

    # Variables
    variable_names = linopy_model.variables.labels
    assert "generator_power" in variable_names
    assert "battery_power_in" in variable_names
    assert "battery_power_out" in variable_names
    assert "battery_soc" in variable_names
    assert "battery_charge_mode" in variable_names

    # Constraints
    constraint_names = linopy_model.constraints.labels
    assert "power_balance_constraint" in constraint_names
    assert "generator_max_power_constraint" in constraint_names
    assert "battery_max_charge_constraint" in constraint_names
    assert "battery_max_discharge_constraint" in constraint_names
    assert "battery_soc_dynamics_constraint" in constraint_names
    assert "battery_capacity_constraint" in constraint_names
    assert "battery_soc_end_constraint" in constraint_names
    assert "battery_soc_start_constraint" in constraint_names

    # Objective
    assert linopy_model.objective is not None


def test_model_already_built(energy_system_sample: ValidatedEnergySystem) -> None:
    model_builder = EnergyAlgebraicModelBuilder(
        energy_system_sample.energy_system_parameters,
    )
    model_builder.build()
    with pytest.raises(AttributeError, match=r"Model has already been built."):
        model_builder.build()


def test_only_generators() -> None:
    pass


def test_only_batteries() -> None:
    pass
