"""Unit tests for the stationary storage formulation and the shared battery model."""

import logging
from datetime import timedelta

import linopy
import pytest
import xarray as xr
from linopy.testing import assert_conequal

from odys import (
    Battery,
    LoadProfile,
    Scenario,
)
from odys.domain.entities.fixed_load import FixedLoad
from odys.domain.entities.generator import Generator
from odys.domain.entities.portfolio import AssetPortfolio
from odys.domain.entities.stationary_storage import StationaryStorage
from odys.energy_system import EnergySystem
from odys.optimization.formulations.stationary_storage import StationaryStorageFormulation
from odys.optimization.model.model_builder import build_model
from odys.optimization.problem import OptimizationProblem

logger = logging.getLogger(__name__)


@pytest.fixture
def storage1() -> StationaryStorage:
    return StationaryStorage(
        name="batt1",
        battery=Battery(
            max_charge_power=200.0,
            max_discharge_power=200.0,
            capacity=100.0,
            efficiency_charging=0.9,
            efficiency_discharging=0.8,
            soc_start=0.25,
            soc_end=0.5,
            soc_min=0.1,
            soc_max=0.9,
        ),
    )


@pytest.fixture
def asset_portfolio_sample(
    generator1: Generator,
    generator2: Generator,
    storage1: StationaryStorage,
    load1: FixedLoad,
) -> AssetPortfolio:
    return AssetPortfolio(assets=[generator1, generator2, storage1, load1])


@pytest.fixture
def energy_system_sample(
    asset_portfolio_sample: AssetPortfolio,
    demand_profile_sample: list[float],
    load1: FixedLoad,
) -> EnergySystem:
    return EnergySystem(
        portfolio=asset_portfolio_sample,
        number_of_steps=len(demand_profile_sample),
        timestep=timedelta(hours=1),
        scenarios=Scenario(profiles=(LoadProfile(load=load1, values=demand_profile_sample),)),
    )


class TestStationaryStorageFormulationConstraints:
    @pytest.fixture(autouse=True)
    def setup(self, linopy_model: linopy.Model, storage1: StationaryStorage, time_index: list[int]) -> None:
        self.linopy_model = linopy_model
        self.storage1 = storage1
        self.time_index = time_index

    def test_constraint_storage_charge_limit(self) -> None:
        actual_constraint = self.linopy_model.constraints["stationary_storage_max_charge_constraint"]

        storage_charge = self.linopy_model.variables["stationary_storage_power_in"]
        storage_charge_mode = self.linopy_model.variables["stationary_storage_charge_mode"]

        expected_expr = storage_charge <= storage_charge_mode * self.storage1.battery.max_charge_power

        assert_conequal(expected_expr, actual_constraint.lhs <= actual_constraint.rhs)

    def test_constraint_storage_discharge_limit(self) -> None:
        actual_constraint = self.linopy_model.constraints["stationary_storage_max_discharge_constraint"]

        storage_discharge = self.linopy_model.variables["stationary_storage_power_out"]
        storage_charge_mode = self.linopy_model.variables["stationary_storage_charge_mode"]

        expected_expr = (
            storage_discharge + storage_charge_mode * self.storage1.battery.max_discharge_power
            <= self.storage1.battery.max_discharge_power
        )

        assert_conequal(expected_expr, actual_constraint.lhs <= actual_constraint.rhs)

    def test_constraint_storage_soc_dynamics(self) -> None:
        actual_constraint = self.linopy_model.constraints["stationary_storage_soc_dynamics_constraint"]
        assert isinstance(actual_constraint, linopy.Constraint)

        storage_soc = self.linopy_model.variables["stationary_storage_soc"]
        storage_charge = self.linopy_model.variables["stationary_storage_power_in"]
        storage_discharge = self.linopy_model.variables["stationary_storage_power_out"]

        eff_ch = self.storage1.battery.efficiency_charging
        eff_disch = self.storage1.battery.efficiency_discharging
        dt = 1.0  # timestep in hours
        self_discharge_rate = self.storage1.battery.self_discharge_rate or 0.0

        for t in self.time_index[1:]:  # Skip t=0
            actual_t = actual_constraint.sel(time=str(t), stationary_storage="batt1", drop=True)

            soc_t = storage_soc.sel(time=str(t), stationary_storage="batt1", drop=True)
            soc_t_minus_1 = storage_soc.sel(time=str(t - 1), stationary_storage="batt1", drop=True)
            storage_charge_t = storage_charge.sel(time=str(t), stationary_storage="batt1", drop=True)
            storage_discharge_t = storage_discharge.sel(time=str(t), stationary_storage="batt1", drop=True)
            capacity = self.storage1.battery.capacity
            expected_expr = (
                soc_t
                == soc_t_minus_1 * (1 - self_discharge_rate * dt)
                + eff_ch * storage_charge_t * dt / capacity
                - 1 / eff_disch * storage_discharge_t * dt / capacity
            )

            assert_conequal(expected_expr, actual_t.lhs == actual_t.rhs)

    def test_constraint_storage_capacity(self) -> None:
        actual_constraint = self.linopy_model.constraints["stationary_storage_capacity_constraint"]

        storage_soc = self.linopy_model.variables["stationary_storage_soc"]
        expected_expr = storage_soc <= 1

        assert_conequal(expected_expr, actual_constraint.lhs <= actual_constraint.rhs)

    def test_constraint_storage_soc_end(self) -> None:
        actual_constraint = self.linopy_model.constraints["stationary_storage_soc_end_constraint"]

        storage_soc = self.linopy_model.variables["stationary_storage_soc"]
        soc_end = storage_soc.sel(time=str(self.time_index[-1]))
        expected_expr = soc_end == self.storage1.battery.soc_end

        assert_conequal(expected_expr, actual_constraint.lhs == actual_constraint.rhs)

    def test_constraint_storage_soc_start(self) -> None:
        actual_constraint = self.linopy_model.constraints["stationary_storage_soc_start_constraint"]

        storage_soc = self.linopy_model.variables["stationary_storage_soc"]
        storage_charge = self.linopy_model.variables["stationary_storage_power_in"]
        storage_discharge = self.linopy_model.variables["stationary_storage_power_out"]

        eff_ch = self.storage1.battery.efficiency_charging
        eff_disch = self.storage1.battery.efficiency_discharging

        t0 = self.time_index[0]
        soc_t0 = storage_soc.sel(time=str(t0))
        storage_charge_t = storage_charge.sel(time=str(t0))
        storage_discharge_t = storage_discharge.sel(time=str(t0))

        storage_soc_start_array = xr.DataArray(
            [[self.storage1.battery.soc_start]],  # [scenarios, storages]
            coords={
                "scenario": ["base"],
                "stationary_storage": [self.storage1.name],
            },
            dims=["scenario", "stationary_storage"],
        )
        capacity = self.storage1.battery.capacity
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
        actual_constraint = self.linopy_model.constraints["stationary_storage_soc_min_constraint"]

        storage_soc = self.linopy_model.variables["stationary_storage_soc"]
        storage_soc_min_array = xr.DataArray(
            [self.storage1.battery.soc_min],
            coords={"stationary_storage": [self.storage1.name]},
            dims=["stationary_storage"],
        )
        expected_expr = storage_soc >= storage_soc_min_array

        assert_conequal(expected_expr, actual_constraint.lhs >= actual_constraint.rhs)

    def test_constraint_storage_soc_max(self) -> None:
        actual_constraint = self.linopy_model.constraints["stationary_storage_soc_max_constraint"]

        storage_soc = self.linopy_model.variables["stationary_storage_soc"]
        storage_soc_max_array = xr.DataArray(
            [self.storage1.battery.soc_max],
            coords={"stationary_storage": [self.storage1.name]},
            dims=["stationary_storage"],
        )
        expected_expr = storage_soc <= storage_soc_max_array

        assert_conequal(expected_expr, actual_constraint.lhs <= actual_constraint.rhs)


class TestStationaryStorageConstraintsSubHourlyTimestep:
    """Verify that SOC constraints correctly scale with a 15-minute timestep."""

    @pytest.fixture
    def energy_system_15min(
        self,
        asset_portfolio_sample: AssetPortfolio,
        demand_profile_sample: list[float],
        load1: FixedLoad,
    ) -> EnergySystem:
        return EnergySystem(
            portfolio=asset_portfolio_sample,
            number_of_steps=len(demand_profile_sample),
            timestep=timedelta(minutes=15),
            scenarios=Scenario(profiles=(LoadProfile(load=load1, values=demand_profile_sample),)),
        )

    @pytest.fixture
    def linopy_model_15min(
        self,
        energy_system_15min: EnergySystem,
    ) -> linopy.Model:
        problem = energy_system_15min.build_problem()
        return build_model(problem)

    def test_soc_dynamics_with_15min_timestep(
        self,
        linopy_model_15min: linopy.Model,
        storage1: StationaryStorage,
        time_index: list[int],
    ) -> None:
        actual_constraint = linopy_model_15min.constraints["stationary_storage_soc_dynamics_constraint"]
        assert isinstance(actual_constraint, linopy.Constraint)

        storage_soc = linopy_model_15min.variables["stationary_storage_soc"]
        storage_charge = linopy_model_15min.variables["stationary_storage_power_in"]
        storage_discharge = linopy_model_15min.variables["stationary_storage_power_out"]

        eff_ch = storage1.battery.efficiency_charging
        eff_disch = storage1.battery.efficiency_discharging
        dt = 0.25  # 15 minutes in hours
        self_discharge_rate = storage1.battery.self_discharge_rate or 0.0

        capacity = storage1.battery.capacity

        for t in time_index[1:]:
            actual_t = actual_constraint.sel(time=str(t), stationary_storage="batt1", drop=True)

            soc_t = storage_soc.sel(time=str(t), stationary_storage="batt1", drop=True)
            soc_t_minus_1 = storage_soc.sel(time=str(t - 1), stationary_storage="batt1", drop=True)
            charge_t = storage_charge.sel(time=str(t), stationary_storage="batt1", drop=True)
            discharge_t = storage_discharge.sel(time=str(t), stationary_storage="batt1", drop=True)

            expected_expr = (
                soc_t
                == soc_t_minus_1 * (1 - self_discharge_rate * dt)
                + eff_ch * charge_t * dt / capacity
                - 1 / eff_disch * discharge_t * dt / capacity
            )

            assert_conequal(expected_expr, actual_t.lhs == actual_t.rhs)

    def test_soc_start_with_15min_timestep(
        self,
        linopy_model_15min: linopy.Model,
        storage1: StationaryStorage,
        time_index: list[int],
    ) -> None:
        actual_constraint = linopy_model_15min.constraints["stationary_storage_soc_start_constraint"]

        storage_soc = linopy_model_15min.variables["stationary_storage_soc"]
        storage_charge = linopy_model_15min.variables["stationary_storage_power_in"]
        storage_discharge = linopy_model_15min.variables["stationary_storage_power_out"]

        eff_ch = storage1.battery.efficiency_charging
        eff_disch = storage1.battery.efficiency_discharging
        dt = 0.25  # 15 minutes in hours
        capacity = storage1.battery.capacity

        t0 = time_index[0]
        soc_t0 = storage_soc.sel(time=str(t0))
        charge_t0 = storage_charge.sel(time=str(t0))
        discharge_t0 = storage_discharge.sel(time=str(t0))

        soc_start_array = xr.DataArray(
            [[storage1.battery.soc_start]],
            coords={
                "scenario": ["base"],
                "stationary_storage": [storage1.name],
            },
            dims=["scenario", "stationary_storage"],
        )

        expected_expr = (
            soc_t0 - soc_start_array - eff_ch * charge_t0 * dt / capacity + 1 / eff_disch * discharge_t0 * dt / capacity
            == 0
        )

        assert_conequal(expected_expr, actual_constraint.lhs == actual_constraint.rhs)


class TestStorageSocEndOptional:
    """Verify the soc_end constraint only covers storages that define a final SOC target."""

    @pytest.fixture
    def storage_without_soc_end(self) -> StationaryStorage:
        return StationaryStorage(
            name="batt_free_end",
            battery=Battery(max_charge_power=200.0, max_discharge_power=200.0, capacity=100.0, soc_start=0.5),
        )

    def _build_linopy_model(
        self,
        storages: list[StationaryStorage],
        generator1: Generator,
        load1: FixedLoad,
        demand_profile_sample: list[float],
    ) -> linopy.Model:
        energy_system = EnergySystem(
            portfolio=AssetPortfolio(assets=[generator1, load1, *storages]),
            number_of_steps=len(demand_profile_sample),
            timestep=timedelta(hours=1),
            scenarios=Scenario(profiles=(LoadProfile(load=load1, values=demand_profile_sample),)),
        )
        return build_model(energy_system.build_problem())

    def test_constraint_covers_only_storages_with_soc_end(
        self,
        storage1: StationaryStorage,
        storage_without_soc_end: StationaryStorage,
        generator1: Generator,
        load1: FixedLoad,
        demand_profile_sample: list[float],
    ) -> None:
        linopy_model = self._build_linopy_model(
            [storage1, storage_without_soc_end],
            generator1,
            load1,
            demand_profile_sample,
        )

        actual_constraint = linopy_model.constraints["stationary_storage_soc_end_constraint"]

        assert list(actual_constraint.coords["stationary_storage"].values) == [storage1.name]

        last_time = str(len(demand_profile_sample) - 1)
        soc_last = linopy_model.variables["stationary_storage_soc"].sel(
            time=last_time,
            stationary_storage=[storage1.name],
        )
        expected_expr = soc_last == storage1.battery.soc_end

        assert_conequal(expected_expr, actual_constraint.lhs == actual_constraint.rhs)

    def test_constraint_absent_when_no_storage_has_soc_end(
        self,
        storage_without_soc_end: StationaryStorage,
        generator1: Generator,
        load1: FixedLoad,
        demand_profile_sample: list[float],
    ) -> None:
        linopy_model = self._build_linopy_model(
            [storage_without_soc_end],
            generator1,
            load1,
            demand_profile_sample,
        )

        assert "stationary_storage_soc_end_constraint" not in set(linopy_model.constraints)


def test_stationary_storage_variable_names_match_the_model(
    optimization_problem: OptimizationProblem,
    linopy_model: linopy.Model,
) -> None:
    assert linopy_model is not None
    storages = optimization_problem.formulation_of(StationaryStorageFormulation)
    assert storages is not None
    variables = storages.variables
    assert variables.net_power.name == StationaryStorageFormulation.net_power_name
    assert variables.soc.name == StationaryStorageFormulation.soc_name
    assert variables.charge_mode.name == StationaryStorageFormulation.charge_mode_name
