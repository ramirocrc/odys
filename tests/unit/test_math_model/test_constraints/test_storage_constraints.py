import logging
from datetime import timedelta

import linopy
import pytest
import xarray as xr
from linopy.testing import assert_conequal

from odys import Scenario
from odys.energy_system_models.assets.generator import Generator
from odys.energy_system_models.assets.load import Load
from odys.energy_system_models.assets.portfolio import AssetPortfolio
from odys.energy_system_models.assets.storage import Storage
from odys.energy_system_models.units import PowerUnit
from odys.energy_system_models.validated_energy_system import ValidatedEnergySystem
from odys.math_model.model_builder import EnergyAlgebraicModelBuilder

logger = logging.getLogger(__name__)


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
def asset_portfolio_sample(
    generator1: Generator,
    generator2: Generator,
    storage1: Storage,
    load1: Load,
) -> AssetPortfolio:
    portfolio = AssetPortfolio()
    portfolio.add_assets(generator1)
    portfolio.add_assets(generator2)
    portfolio.add_assets(storage1)
    portfolio.add_assets(load1)
    return portfolio


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
        dt = 1.0  # timestep in hours

        for t in self.time_index[1:]:  # Skip t=0
            actual_t = actual_constraint.sel(time=str(t), storage="batt1")

            soc_t = storage_soc.sel(time=str(t), storage="batt1")
            soc_t_minus_1 = storage_soc.sel(time=str(t - 1), storage="batt1")
            storage_charge_t = storage_charge.sel(time=str(t), storage="batt1")
            storage_discharge_t = storage_discharge.sel(time=str(t), storage="batt1")
            capacity = self.storage1.capacity
            expected_expr = (
                soc_t
                == soc_t_minus_1
                + eff_ch * storage_charge_t * dt / capacity
                - 1 / eff_disch * storage_discharge_t * dt / capacity
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
        dt = 1.0  # timestep in hours
        expected_expr = (
            soc_t0
            - storage_soc_start_array
            - eff_ch * storage_charge_t * dt / capacity
            + 1 / eff_disch * storage_discharge_t * dt / capacity
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


class TestStorageConstraintsSubHourlyTimestep:
    """Verify that SOC constraints correctly scale with a 15-minute timestep."""

    @pytest.fixture
    def energy_system_15min(
        self,
        asset_portfolio_sample: AssetPortfolio,
        demand_profile_sample: list[float],
    ) -> ValidatedEnergySystem:
        return ValidatedEnergySystem(
            portfolio=asset_portfolio_sample,
            number_of_steps=len(demand_profile_sample),
            timestep=timedelta(minutes=15),
            power_unit=PowerUnit.MegaWatt,
            scenarios=Scenario(
                available_capacity_profiles={},
                load_profiles={"load1": demand_profile_sample},
            ),
        )

    @pytest.fixture
    def linopy_model_15min(self, energy_system_15min: ValidatedEnergySystem) -> linopy.Model:

        model_builder = EnergyAlgebraicModelBuilder(
            energy_system_15min.energy_system_parameters,
        )
        return model_builder.build().linopy_model

    def test_soc_dynamics_with_15min_timestep(
        self,
        linopy_model_15min: linopy.Model,
        storage1: Storage,
        time_index: list[int],
    ) -> None:
        actual_constraint = linopy_model_15min.constraints["storage_soc_dynamics_constraint"]

        storage_soc = linopy_model_15min.variables["storage_soc"]
        storage_charge = linopy_model_15min.variables["storage_power_in"]
        storage_discharge = linopy_model_15min.variables["storage_power_out"]

        eff_ch = storage1.efficiency_charging
        eff_disch = storage1.efficiency_discharging
        dt = 0.25  # 15 minutes in hours
        capacity = storage1.capacity

        for t in time_index[1:]:
            actual_t = actual_constraint.sel(time=str(t), storage="batt1")

            soc_t = storage_soc.sel(time=str(t), storage="batt1")
            soc_t_minus_1 = storage_soc.sel(time=str(t - 1), storage="batt1")
            charge_t = storage_charge.sel(time=str(t), storage="batt1")
            discharge_t = storage_discharge.sel(time=str(t), storage="batt1")

            expected_expr = (
                soc_t == soc_t_minus_1 + eff_ch * charge_t * dt / capacity - 1 / eff_disch * discharge_t * dt / capacity
            )

            assert_conequal(expected_expr, actual_t.lhs == actual_t.rhs)

    def test_soc_start_with_15min_timestep(
        self,
        linopy_model_15min: linopy.Model,
        storage1: Storage,
        time_index: list[int],
    ) -> None:
        actual_constraint = linopy_model_15min.constraints["storage_soc_start_constraint"]

        storage_soc = linopy_model_15min.variables["storage_soc"]
        storage_charge = linopy_model_15min.variables["storage_power_in"]
        storage_discharge = linopy_model_15min.variables["storage_power_out"]

        eff_ch = storage1.efficiency_charging
        eff_disch = storage1.efficiency_discharging
        dt = 0.25  # 15 minutes in hours
        capacity = storage1.capacity

        t0 = time_index[0]
        soc_t0 = storage_soc.sel(time=str(t0))
        charge_t0 = storage_charge.sel(time=str(t0))
        discharge_t0 = storage_discharge.sel(time=str(t0))

        soc_start_array = xr.DataArray(
            [[storage1.soc_start]],
            coords={
                "scenario": ["deterministic_scenario"],
                "storage": [storage1.name],
            },
            dims=["scenario", "storage"],
        )

        expected_expr = (
            soc_t0 - soc_start_array - eff_ch * charge_t0 * dt / capacity + 1 / eff_disch * discharge_t0 * dt / capacity
            == 0
        )

        assert_conequal(expected_expr, actual_constraint.lhs == actual_constraint.rhs)
