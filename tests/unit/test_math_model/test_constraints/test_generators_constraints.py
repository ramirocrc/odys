import logging
from datetime import timedelta

import linopy
import pytest
import xarray as xr
from linopy.testing import assert_conequal

from odis._math_model.model_builder import EnergyAlgebraicModelBuilder
from odis.energy_system_models.assets.generator import PowerGenerator
from odis.energy_system_models.assets.load import Load
from odis.energy_system_models.assets.portfolio import AssetPortfolio
from odis.energy_system_models.scenarios import Scenario
from odis.energy_system_models.units import PowerUnit
from odis.energy_system_models.validated_energy_system import ValidatedEnergySystem

logger = logging.getLogger(__name__)


@pytest.fixture
def generator1() -> PowerGenerator:
    return PowerGenerator(
        name="gen1",
        nominal_power=100.0,
        variable_cost=20.0,
        min_power=10.0,
        min_up_time=2,
        ramp_up=50.0,
        ramp_down=40.0,
    )


@pytest.fixture
def generator2() -> PowerGenerator:
    return PowerGenerator(
        name="gen2",
        nominal_power=150.0,
        variable_cost=25.0,
        min_power=15.0,
        min_up_time=3,
        ramp_up=75.0,
        ramp_down=60.0,
    )


@pytest.fixture
def load1() -> Load:
    return Load(name="load1")


@pytest.fixture
def asset_portfolio_sample(
    generator1: PowerGenerator,
    generator2: PowerGenerator,
    load1: Load,
) -> AssetPortfolio:
    portfolio = AssetPortfolio()
    portfolio.add_asset(generator1)
    portfolio.add_asset(generator2)
    portfolio.add_asset(load1)
    return portfolio


@pytest.fixture
def demand_profile_sample() -> list[float]:
    return [150, 200, 150]


@pytest.fixture
def time_index(demand_profile_sample: list[float]) -> list[int]:
    return list(range(len(demand_profile_sample)))


@pytest.fixture
def demand_profile_extended() -> list[float]:
    return [100, 150, 200, 180, 160]


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


class TestGeneratorConstraints:
    @pytest.fixture(autouse=True)
    def setup(
        self,
        linopy_model: linopy.Model,
        generator1: PowerGenerator,
        generator2: PowerGenerator,
        time_index: list[int],
    ) -> None:
        self.linopy_model = linopy_model
        self.generator1 = generator1
        self.generator2 = generator2
        self.time_index = time_index

    def test_constraint_generator_limit(self) -> None:
        actual_constraint = self.linopy_model.constraints["generator_max_power_constraint"]

        generator_power = self.linopy_model.variables["generator_power"]
        generator_status = self.linopy_model.variables["generator_status"]

        nominal_powers = [self.generator1.nominal_power, self.generator2.nominal_power]
        nominal_power_array = xr.DataArray(
            nominal_powers,
            coords={"generator": [self.generator1.name, self.generator2.name]},
        )

        expected_expr = generator_power <= generator_status * nominal_power_array  # pyright: ignore reportOperatorIssue
        assert_conequal(expected_expr, actual_constraint.lhs <= actual_constraint.rhs)

    def test_constraint_generator_status(self) -> None:
        actual_constraint = self.linopy_model.constraints["generator_status_constraint"]

        generator_power = self.linopy_model.variables["generator_power"]
        generator_status = self.linopy_model.variables["generator_status"]

        nominal_powers = [self.generator1.nominal_power, self.generator2.nominal_power]
        nominal_power_array = xr.DataArray(
            nominal_powers,
            coords={"generator": [self.generator1.name, self.generator2.name]},
        )

        epsilon = 1e-5 * nominal_power_array
        expected_expr = generator_power >= generator_status * epsilon  #  pyright: ignore reportOperatorIssue
        assert_conequal(expected_expr, actual_constraint.lhs >= actual_constraint.rhs)

    def test_constraint_generator_startup_lower_bound(self) -> None:
        actual_constraint = self.linopy_model.constraints["generator_startup_lower_bound_constraint"]

        generator_startup = self.linopy_model.variables["generator_startup"]
        generator_status = self.linopy_model.variables["generator_status"]

        expected_expr = generator_startup >= generator_status - generator_status.shift(time=1)
        assert_conequal(expected_expr, actual_constraint.lhs >= actual_constraint.rhs)

    def test_constraint_generator_startup_upper_bound_1(self) -> None:
        actual_constraint = self.linopy_model.constraints["generator_startup_upper_bound_1_constraint"]

        generator_startup = self.linopy_model.variables["generator_startup"]
        generator_status = self.linopy_model.variables["generator_status"]

        expected_expr = generator_startup <= generator_status
        assert_conequal(expected_expr, actual_constraint.lhs <= actual_constraint.rhs)

    def test_constraint_generator_startup_upper_bound_2(self) -> None:
        actual_constraint = self.linopy_model.constraints["generator_startup_upper_bound_2_constraint"]

        generator_startup = self.linopy_model.variables["generator_startup"]
        generator_status = self.linopy_model.variables["generator_status"]

        expected_expr = generator_startup + generator_status.shift(time=1) <= 1.0
        assert_conequal(expected_expr, actual_constraint.lhs <= actual_constraint.rhs)

    def test_constraint_generator_shutdown_lower_bound(self) -> None:
        actual_constraint = self.linopy_model.constraints["generator_shutdown_lower_bound_constraint"]

        generator_shutdown = self.linopy_model.variables["generator_shutdown"]
        generator_status = self.linopy_model.variables["generator_status"]

        expected_expr = generator_shutdown >= generator_status.shift(time=1) - generator_status
        assert_conequal(expected_expr, actual_constraint.lhs >= actual_constraint.rhs)

    def test_constraint_generator_shutdown_upper_bound_1(self) -> None:
        actual_constraint = self.linopy_model.constraints["generator_shutdown_upper_bound_1_constraint"]

        generator_shutdown = self.linopy_model.variables["generator_shutdown"]
        generator_status = self.linopy_model.variables["generator_status"]

        expected_expr = generator_shutdown <= generator_status.shift(time=1)
        assert_conequal(expected_expr, actual_constraint.lhs <= actual_constraint.rhs)

    def test_constraint_generator_shutdown_upper_bound_2(self) -> None:
        actual_constraint = self.linopy_model.constraints["generator_shutdown_upper_bound_2_constraint"]

        generator_shutdown = self.linopy_model.variables["generator_shutdown"]
        generator_status = self.linopy_model.variables["generator_status"]

        expected_expr = generator_shutdown + generator_status <= 1.0
        assert_conequal(expected_expr, actual_constraint.lhs <= actual_constraint.rhs)

    def test_constraint_generator_min_uptime(self) -> None:
        gen1_constraint_name = f"generator_min_uptime_{self.generator1.name}_constraint"
        gen2_constraint_name = f"generator_min_uptime_{self.generator2.name}_constraint"

        gen1_actual_constraint = self.linopy_model.constraints[gen1_constraint_name]
        gen2_actual_constraint = self.linopy_model.constraints[gen2_constraint_name]

        generator_status = self.linopy_model.variables["generator_status"]
        generator_shutdown = self.linopy_model.variables["generator_shutdown"]

        gen1_status = generator_status.sel(generator=self.generator1.name)
        gen1_shutdown = generator_shutdown.sel(generator=self.generator1.name)
        gen1_expected_expr = gen1_status.rolling(
            time=self.generator1.min_up_time,
        ).sum() >= self.generator1.min_up_time * gen1_shutdown.shift(time=-1)
        assert_conequal(gen1_expected_expr, gen1_actual_constraint.lhs >= gen1_actual_constraint.rhs)

        gen2_status = generator_status.sel(generator=self.generator2.name)
        gen2_shutdown = generator_shutdown.sel(generator=self.generator2.name)
        gen2_expected_expr = gen2_status.rolling(
            time=self.generator2.min_up_time,
        ).sum() >= self.generator2.min_up_time * gen2_shutdown.shift(time=-1)
        assert_conequal(gen2_expected_expr, gen2_actual_constraint.lhs >= gen2_actual_constraint.rhs)

    def test_constraint_generator_min_power(self) -> None:
        actual_constraint = self.linopy_model.constraints["generator_min_power_constraint"]

        generator_power = self.linopy_model.variables["generator_power"]
        generator_status = self.linopy_model.variables["generator_status"]

        min_powers = [self.generator1.min_power, self.generator2.min_power]
        min_power_array = xr.DataArray(
            min_powers,
            coords={"generator": [self.generator1.name, self.generator2.name]},
        )

        expected_expr = generator_power >= min_power_array * generator_status
        assert_conequal(expected_expr, actual_constraint.lhs >= actual_constraint.rhs)

    def test_constraint_generator_max_ramp_up(self) -> None:
        actual_constraint = self.linopy_model.constraints["generator_max_ramp_up_constraint"]

        generator_power = self.linopy_model.variables["generator_power"]

        max_ramp_ups = [self.generator1.ramp_up, self.generator2.ramp_up]
        max_ramp_up_array = xr.DataArray(
            max_ramp_ups,
            coords={"generator": [self.generator1.name, self.generator2.name]},
        )

        expected_expr = generator_power - generator_power.shift(time=1) <= max_ramp_up_array
        assert_conequal(expected_expr, actual_constraint.lhs <= actual_constraint.rhs)

    def test_constraint_generator_max_ramp_down(self) -> None:
        actual_constraint = self.linopy_model.constraints["generator_max_ramp_down_constraint"]

        generator_power = self.linopy_model.variables["generator_power"]

        max_ramp_downs = [self.generator1.ramp_down, self.generator2.ramp_down]
        max_ramp_down_array = xr.DataArray(
            max_ramp_downs,
            coords={"generator": [self.generator1.name, self.generator2.name]},
        )

        expected_expr = generator_power.shift(time=1) - generator_power <= max_ramp_down_array
        assert_conequal(expected_expr, actual_constraint.lhs <= actual_constraint.rhs)
