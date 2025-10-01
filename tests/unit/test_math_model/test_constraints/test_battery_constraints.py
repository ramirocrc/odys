import logging
from datetime import timedelta

import linopy
import pytest
import xarray as xr
from linopy.testing import assert_conequal

from optimes._math_model.model_builder import EnergyAlgebraicModelBuilder
from optimes.energy_system_models.assets.generator import PowerGenerator
from optimes.energy_system_models.assets.portfolio import AssetPortfolio
from optimes.energy_system_models.assets.storage import Battery
from optimes.energy_system_models.units import PowerUnit
from optimes.energy_system_models.validated_energy_system import ValidatedEnergySystem

logger = logging.getLogger(__name__)


@pytest.fixture
def generator1() -> PowerGenerator:
    return PowerGenerator(
        name="gen1",
        nominal_power=100.0,
        variable_cost=20.0,
    )


@pytest.fixture
def generator2() -> PowerGenerator:
    return PowerGenerator(
        name="gen2",
        nominal_power=150.0,
        variable_cost=25.0,
    )


@pytest.fixture
def battery1() -> Battery:
    return Battery(
        name="batt1",
        max_power=200.0,
        capacity=100.0,
        efficiency_charging=0.9,
        efficiency_discharging=0.8,
        soc_start=25.0,
        soc_end=50.0,
        soc_min=10.0,
        soc_max=90.0,
    )


@pytest.fixture
def asset_portfolio_sample(
    generator1: PowerGenerator,
    generator2: PowerGenerator,
    battery1: Battery,
) -> AssetPortfolio:
    portfolio = AssetPortfolio()
    portfolio.add_asset(generator1)
    portfolio.add_asset(generator2)
    portfolio.add_asset(battery1)
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
        demand_profile=demand_profile_sample,
        timestep=timedelta(hours=1),
        power_unit=PowerUnit.MegaWatt,
    )


@pytest.fixture
def linopy_model(energy_system_sample: ValidatedEnergySystem) -> linopy.Model:
    model_builder = EnergyAlgebraicModelBuilder(energy_system_sample.parameters)
    return model_builder.build()


class TestBatteryConstraints:
    @pytest.fixture(autouse=True)
    def setup(self, linopy_model: linopy.Model, battery1: Battery, time_index: list[int]) -> None:
        self.linopy_model = linopy_model
        self.battery1 = battery1
        self.time_index = time_index

    def test_constraint_battery_charge_limit(self) -> None:
        actual_constraint = self.linopy_model.constraints["battery_max_charge_constraint"]

        battery_charge = self.linopy_model.variables["battery_power_in"]
        battery_charge_mode = self.linopy_model.variables["battery_charge_mode"]

        expected_expr = battery_charge <= battery_charge_mode * self.battery1.max_power

        assert_conequal(expected_expr, actual_constraint.lhs <= actual_constraint.rhs)

    def test_constraint_battery_discharge_limit(self) -> None:
        actual_constraint = self.linopy_model.constraints["battery_max_discharge_constraint"]

        battery_discharge = self.linopy_model.variables["battery_power_out"]
        battery_charge_mode = self.linopy_model.variables["battery_charge_mode"]

        expected_expr = battery_discharge + battery_charge_mode * self.battery1.max_power <= self.battery1.max_power

        assert_conequal(expected_expr, actual_constraint.lhs <= actual_constraint.rhs)

    def test_constraint_battery_soc_dynamics(self) -> None:
        actual_constraint = self.linopy_model.constraints["battery_soc_dynamics_constraint"]

        battery_soc = self.linopy_model.variables["battery_soc"]
        battery_charge = self.linopy_model.variables["battery_power_in"]
        battery_discharge = self.linopy_model.variables["battery_power_out"]

        eff_ch = self.battery1.efficiency_charging
        eff_disch = self.battery1.efficiency_discharging

        for t in self.time_index[1:]:  # Skip t=0
            actual_t = actual_constraint.sel(time=str(t), batteries="batt1")

            bat_soc_t = battery_soc.sel(time=str(t), batteries="batt1")
            bat_soc_t_minus_1 = battery_soc.sel(time=str(t - 1), batteries="batt1")
            battery_charge_t = battery_charge.sel(time=str(t), batteries="batt1")
            battery_discharge_t = battery_discharge.sel(time=str(t), batteries="batt1")
            expected_expr = (
                bat_soc_t == bat_soc_t_minus_1 + eff_ch * battery_charge_t - 1 / eff_disch * battery_discharge_t
            )

            assert_conequal(expected_expr, actual_t.lhs == actual_t.rhs)

    def test_constraint_battery_capacity(self) -> None:
        actual_constraint = self.linopy_model.constraints["battery_capacity_constraint"]

        battery_soc = self.linopy_model.variables["battery_soc"]
        expected_expr = battery_soc <= self.battery1.capacity

        assert_conequal(expected_expr, actual_constraint.lhs <= actual_constraint.rhs)

    def test_constraint_battery_soc_end(self) -> None:
        actual_constraint = self.linopy_model.constraints["battery_soc_end_constraint"]

        battery_soc = self.linopy_model.variables["battery_soc"]
        soc_end = battery_soc.sel(time=str(self.time_index[-1]))
        expected_expr = soc_end == self.battery1.soc_end

        assert_conequal(expected_expr, actual_constraint.lhs == actual_constraint.rhs)

    def test_constraint_battery_soc_start(self) -> None:
        actual_constraint = self.linopy_model.constraints["battery_soc_start_constraint"]

        battery_soc = self.linopy_model.variables["battery_soc"]
        battery_charge = self.linopy_model.variables["battery_power_in"]
        battery_discharge = self.linopy_model.variables["battery_power_out"]

        eff_ch = self.battery1.efficiency_charging
        eff_disch = self.battery1.efficiency_discharging

        t0 = self.time_index[0]
        bat_soc_t0 = battery_soc.sel(time=str(t0))
        battery_charge_t = battery_charge.sel(time=str(t0))
        battery_discharge_t = battery_discharge.sel(time=str(t0))

        battery_soc_start_array = xr.DataArray(
            [[self.battery1.soc_start]],  # [scenarios, batteries]
            coords={
                "scenarios": ["deterministic_scenario"],
                "batteries": [self.battery1.name],
            },
            dims=["scenarios", "batteries"],
        )
        expected_expr = (
            bat_soc_t0 - battery_soc_start_array - eff_ch * battery_charge_t + 1 / eff_disch * battery_discharge_t == 0
        )

        assert_conequal(expected_expr, actual_constraint.lhs == actual_constraint.rhs)

    def test_constraint_battery_soc_min(self) -> None:
        actual_constraint = self.linopy_model.constraints["batter_soc_min_constraint"]

        battery_soc = self.linopy_model.variables["battery_soc"]
        battery_soc_min_array = xr.DataArray(
            [self.battery1.soc_min],
            coords={"batteries": [self.battery1.name]},
            dims=["batteries"],
        )
        expected_expr = battery_soc >= battery_soc_min_array

        assert_conequal(expected_expr, actual_constraint.lhs >= actual_constraint.rhs)

    def test_constraint_battery_soc_max(self) -> None:
        actual_constraint = self.linopy_model.constraints["batter_soc_max_constraint"]

        battery_soc = self.linopy_model.variables["battery_soc"]
        battery_soc_max_array = xr.DataArray(
            [self.battery1.soc_max],
            coords={"batteries": [self.battery1.name]},
            dims=["batteries"],
        )
        expected_expr = battery_soc <= battery_soc_max_array

        assert_conequal(expected_expr, actual_constraint.lhs <= actual_constraint.rhs)
