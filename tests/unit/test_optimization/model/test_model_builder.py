import logging
from datetime import timedelta

import pytest

from odys.domain.entities.charger import Charger
from odys.domain.entities.electric_vehicle import ElectricVehicle
from odys.domain.entities.fixed_load import FixedLoad
from odys.domain.entities.generator import Generator
from odys.domain.entities.portfolio import AssetPortfolio
from odys.domain.entities.standalone_storage import StandaloneStorage
from odys.domain.exceptions import OdysError
from odys.domain.scenarios import Scenario
from odys.energy_system import EnergySystem
from odys.optimization.model.dimensions import ModelDimension
from odys.optimization.model.model_builder import EnergyAlgebraicModelBuilder

logger = logging.getLogger(__name__)


@pytest.fixture
def load1() -> FixedLoad:
    return FixedLoad(name="load1")


@pytest.fixture
def asset_portfolio_sample(load1: FixedLoad) -> AssetPortfolio:
    return AssetPortfolio(
        assets=[
            Generator(
                name="gen1",
                nominal_power=100.0,
                variable_cost=20.0,
            ),
            Generator(
                name="gen2",
                nominal_power=150.0,
                variable_cost=25.0,
            ),
            StandaloneStorage(
                name="battery1",
                max_charge_power=200.0,
                max_discharge_power=200.0,
                capacity=100.0,
                efficiency_charging=1,
                efficiency_discharging=1,
                soc_start=1.0,
                soc_end=0.5,
            ),
            load1,
        ],
    )


@pytest.fixture
def energy_system_sample(asset_portfolio_sample: AssetPortfolio) -> EnergySystem:
    demand_profile = [150, 200, 150]
    return EnergySystem(
        portfolio=asset_portfolio_sample,
        number_of_steps=len(demand_profile),
        timestep=timedelta(hours=1),
        scenarios=Scenario(
            available_capacity_profiles={},
            fixed_load_profiles={"load1": demand_profile},
        ),
    )


def test_model_build_components(
    energy_system_sample: EnergySystem,
) -> None:
    params = energy_system_sample.build_parameters()
    model_builder = EnergyAlgebraicModelBuilder(energy_system_parameters=params)
    energy_milp_model = model_builder.build()
    linopy_model = energy_milp_model.linopy_model

    # Variables
    variable_names = linopy_model.variables.labels
    assert "generator_power" in variable_names
    assert "standalone_storage_power_in" in variable_names
    assert "standalone_storage_power_out" in variable_names
    assert "standalone_storage_soc" in variable_names
    assert "standalone_storage_charge_mode" in variable_names
    assert "charger_ev_assignment" not in variable_names

    # Constraints
    constraint_names = linopy_model.constraints.labels
    assert "power_balance_constraint" in constraint_names
    assert "generator_max_power_constraint" in constraint_names
    assert "standalone_storage_max_charge_constraint" in constraint_names
    assert "standalone_storage_max_discharge_constraint" in constraint_names
    assert "standalone_storage_soc_dynamics_constraint" in constraint_names
    assert "standalone_storage_capacity_constraint" in constraint_names
    assert "standalone_storage_soc_end_constraint" in constraint_names
    assert "standalone_storage_soc_start_constraint" in constraint_names

    # Objective
    assert linopy_model.objective is not None


def test_model_build_with_ev_fleet(load1: FixedLoad) -> None:
    demand_profile = [50, 80, 60]
    ev_names = ["ev1", "ev2"]
    charger_names = ["charger1"]
    energy_system = EnergySystem(
        portfolio=AssetPortfolio(
            assets=[
                Generator(name="gen1", nominal_power=200.0, variable_cost=20.0),
                *[
                    ElectricVehicle(
                        name=name,
                        capacity=50.0,
                        max_charge_power=22.0,
                        max_discharge_power=0.0,
                        soc_start=0.5,
                        trips=(),
                    )
                    for name in ev_names
                ],
                *[Charger(name=name, max_power=22.0) for name in charger_names],
                load1,
            ],
        ),
        number_of_steps=len(demand_profile),
        timestep=timedelta(hours=1),
        scenarios=Scenario(
            available_capacity_profiles={},
            fixed_load_profiles={"load1": demand_profile},
        ),
    )
    model_builder = EnergyAlgebraicModelBuilder(energy_system_parameters=energy_system.build_parameters())
    energy_milp_model = model_builder.build()

    assert "charger_ev_assignment" in energy_milp_model.linopy_model.variables.labels

    assignment = energy_milp_model.vars.charger_ev_assignment
    assert assignment.attrs["binary"]
    assert set(assignment.dims) == {
        ModelDimension.Scenarios.value,
        ModelDimension.Time.value,
        ModelDimension.Chargers.value,
        ModelDimension.EVs.value,
    }
    assert list(assignment.coords[ModelDimension.Chargers.value].values) == charger_names
    assert list(assignment.coords[ModelDimension.EVs.value].values) == ev_names


def test_model_already_built(
    energy_system_sample: EnergySystem,
) -> None:
    params = energy_system_sample.build_parameters()
    model_builder = EnergyAlgebraicModelBuilder(energy_system_parameters=params)
    model_builder.build()
    with pytest.raises(OdysError, match=r"Model has already been built."):
        model_builder.build()
