import logging
from datetime import timedelta

import linopy
import pytest
import xarray as xr
from linopy.testing import assert_conequal

from odys.energy_system_models.assets.generator import Generator
from odys.energy_system_models.assets.load import Load
from odys.energy_system_models.assets.portfolio import AssetPortfolio
from odys.energy_system_models.assets.storage import Storage
from odys.energy_system_models.scenarios import Scenario
from odys.energy_system_models.units import PowerUnit
from odys.energy_system_models.validated_energy_system import ValidatedEnergySystem
from odys.math_model.model_builder import EnergyAlgebraicModelBuilder

logger = logging.getLogger(__name__)


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
def storage1() -> Storage:
    return Storage(
        name="batt1",
        max_power=200.0,
        capacity=100.0,
        efficiency_charging=0.9,
        efficiency_discharging=0.8,
        soc_start=0.25,
        soc_end=0.5,
        soc_min=0.1,
        soc_max=0.9,
    )


@pytest.fixture
def load1() -> Load:
    return Load(name="load1")


@pytest.fixture
def asset_portfolio_sample(
    generator1: Generator,
    generator2: Generator,
    storage1: Storage,
    load1: Load,
) -> AssetPortfolio:
    portfolio = AssetPortfolio()
    portfolio.add_asset(generator1)
    portfolio.add_asset(generator2)
    portfolio.add_asset(storage1)
    portfolio.add_asset(load1)
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
        number_of_steps=len(demand_profile_sample),
        timestep=timedelta(hours=1),
        power_unit=PowerUnit.MegaWatt,
        scenarios=Scenario(
            available_capacity_profiles={},
            load_profiles={"load1": demand_profile_sample},
        ),
    )


@pytest.fixture
def linopy_model(energy_system_sample: ValidatedEnergySystem) -> linopy.Model:
    model_builder = EnergyAlgebraicModelBuilder(
        energy_system_sample.energy_system_parameters,
    )

    energy_milp_model = model_builder.build()
    return energy_milp_model.linopy_model


class TestStorageConstraints:
    @pytest.fixture(autouse=True)
    def setup(self, linopy_model: linopy.Model, storage1: Storage, time_index: list[int]) -> None:
        self.linopy_model = linopy_model
        self.storage1 = storage1
        self.time_index = time_index

    def test_constraint_storage_charge_limit(self) -> None:
        actual_constraint = self.linopy_model.constraints["storage_max_charge_constraint"]

        storage_charge = self.linopy_model.variables["storage_power_in"]
        storage_charge_mode = self.linopy_model.variables["storage_charge_mode"]

        expected_expr = storage_charge <= storage_charge_mode * self.storage1.max_power

        assert_conequal(expected_expr, actual_constraint.lhs <= actual_constraint.rhs)

    def test_constraint_storage_discharge_limit(self) -> None:
        actual_constraint = self.linopy_model.constraints["storage_max_discharge_constraint"]

        storage_discharge = self.linopy_model.variables["storage_power_out"]
        storage_charge_mode = self.linopy_model.variables["storage_charge_mode"]

        expected_expr = storage_discharge + storage_charge_mode * self.storage1.max_power <= self.storage1.max_power

        assert_conequal(expected_expr, actual_constraint.lhs <= actual_constraint.rhs)

    def test_constraint_storage_soc_dynamics(self) -> None:
        actual_constraint = self.linopy_model.constraints["storage_soc_dynamics_constraint"]

        storage_soc = self.linopy_model.variables["storage_soc"]
        storage_charge = self.linopy_model.variables["storage_power_in"]
        storage_discharge = self.linopy_model.variables["storage_power_out"]

        eff_ch = self.storage1.efficiency_charging
        eff_disch = self.storage1.efficiency_discharging

        for t in self.time_index[1:]:  # Skip t=0
            actual_t = actual_constraint.sel(time=str(t), storage="batt1")

            soc_t = storage_soc.sel(time=str(t), storage="batt1")
            soc_t_minus_1 = storage_soc.sel(time=str(t - 1), storage="batt1")
            storage_charge_t = storage_charge.sel(time=str(t), storage="batt1")
            storage_discharge_t = storage_discharge.sel(time=str(t), storage="batt1")
            capacity = self.storage1.capacity
            expected_expr = (
                soc_t
                == soc_t_minus_1 + eff_ch * storage_charge_t / capacity - 1 / eff_disch * storage_discharge_t / capacity
            )

            assert_conequal(expected_expr, actual_t.lhs == actual_t.rhs)

    def test_constraint_storage_capacity(self) -> None:
        actual_constraint = self.linopy_model.constraints["storage_capacity_constraint"]

        storage_soc = self.linopy_model.variables["storage_soc"]
        expected_expr = storage_soc <= 1

        assert_conequal(expected_expr, actual_constraint.lhs <= actual_constraint.rhs)

    def test_constraint_storage_soc_end(self) -> None:
        actual_constraint = self.linopy_model.constraints["storage_soc_end_constraint"]

        storage_soc = self.linopy_model.variables["storage_soc"]
        soc_end = storage_soc.sel(time=str(self.time_index[-1]))
        expected_expr = soc_end == self.storage1.soc_end

        assert_conequal(expected_expr, actual_constraint.lhs == actual_constraint.rhs)

    def test_constraint_storage_soc_start(self) -> None:
        actual_constraint = self.linopy_model.constraints["storage_soc_start_constraint"]

        storage_soc = self.linopy_model.variables["storage_soc"]
        storage_charge = self.linopy_model.variables["storage_power_in"]
        storage_discharge = self.linopy_model.variables["storage_power_out"]

        eff_ch = self.storage1.efficiency_charging
        eff_disch = self.storage1.efficiency_discharging

        t0 = self.time_index[0]
        soc_t0 = storage_soc.sel(time=str(t0))
        storage_charge_t = storage_charge.sel(time=str(t0))
        storage_discharge_t = storage_discharge.sel(time=str(t0))

        storage_soc_start_array = xr.DataArray(
            [[self.storage1.soc_start]],  # [scenarios, storages]
            coords={
                "scenario": ["deterministic_scenario"],
                "storage": [self.storage1.name],
            },
            dims=["scenario", "storage"],
        )
        capacity = self.storage1.capacity
        expected_expr = (
            soc_t0
            - storage_soc_start_array
            - eff_ch * storage_charge_t / capacity
            + 1 / eff_disch * storage_discharge_t / capacity
            == 0
        )

        assert_conequal(expected_expr, actual_constraint.lhs == actual_constraint.rhs)

    def test_constraint_storage_soc_min(self) -> None:
        actual_constraint = self.linopy_model.constraints["storage_soc_min_constraint"]

        storage_soc = self.linopy_model.variables["storage_soc"]
        storage_soc_min_array = xr.DataArray(
            [self.storage1.soc_min],
            coords={"storage": [self.storage1.name]},
            dims=["storage"],
        )
        expected_expr = storage_soc >= storage_soc_min_array

        assert_conequal(expected_expr, actual_constraint.lhs >= actual_constraint.rhs)

    def test_constraint_storage_soc_max(self) -> None:
        actual_constraint = self.linopy_model.constraints["storage_soc_max_constraint"]

        storage_soc = self.linopy_model.variables["storage_soc"]
        storage_soc_max_array = xr.DataArray(
            [self.storage1.soc_max],
            coords={"storage": [self.storage1.name]},
            dims=["storage"],
        )
        expected_expr = storage_soc <= storage_soc_max_array

        assert_conequal(expected_expr, actual_constraint.lhs <= actual_constraint.rhs)
