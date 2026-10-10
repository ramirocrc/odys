"""Unit tests for the generator formulation: variables, constraints, power injection and profit."""

import logging
from datetime import timedelta

import linopy
import pytest
import xarray as xr
from linopy.testing import assert_conequal, assert_linequal

from odys.domain.entities.fixed_load import FixedLoad
from odys.domain.entities.generator import Generator
from odys.domain.entities.portfolio import AssetPortfolio
from odys.domain.exceptions import OdysError
from odys.domain.profiles import LoadProfile
from odys.domain.scenario import Scenario
from odys.energy_system import EnergySystem
from odys.optimization.formulations.generator import GeneratorFormulation
from odys.optimization.problem import OptimizationProblem

logger = logging.getLogger(__name__)

HOURS_PER_STEP = 1.0


@pytest.fixture
def generator1() -> Generator:
    """Override conftest generator1 with ramp/min_power/min_up_time/min_down_time params."""
    return Generator(
        name="gen1",
        nominal_power=100.0,
        variable_cost=20.0,
        min_power=10.0,
        min_up_time=2,
        min_down_time=2,
        ramp_up=50.0,
        ramp_down=40.0,
    )


@pytest.fixture
def generator2() -> Generator:
    """Override conftest generator2 with ramp/min_power/min_up_time/min_down_time params."""
    return Generator(
        name="gen2",
        nominal_power=150.0,
        variable_cost=25.0,
        min_power=15.0,
        min_up_time=3,
        min_down_time=3,
        ramp_up=75.0,
        ramp_down=60.0,
    )


@pytest.fixture
def asset_portfolio_sample(
    generator1: Generator,
    generator2: Generator,
    load1: FixedLoad,
) -> AssetPortfolio:
    return AssetPortfolio(assets=[generator1, generator2, load1])


@pytest.fixture
def demand_profile_extended() -> list[float]:
    return [100, 150, 200, 180, 160]


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


class TestGeneratorFormulationConstraints:
    @pytest.fixture(autouse=True)
    def setup(
        self,
        linopy_model: linopy.Model,
        generator1: Generator,
        generator2: Generator,
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

        expected_expr = generator_power <= generator_status * nominal_power_array  # pyrefly: ignore
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
        expected_expr = generator_power >= generator_status * epsilon  # pyrefly: ignore
        assert_conequal(expected_expr, actual_constraint.lhs >= actual_constraint.rhs)

    def test_constraint_generator_startup_lower_bound(self) -> None:
        actual_constraint = self.linopy_model.constraints["generator_startup_lower_bound_constraint"]

        generator_startup = self.linopy_model.variables["generator_startup"]
        generator_status = self.linopy_model.variables["generator_status"]

        expected_expr = generator_startup >= generator_status - (1 * generator_status).shift(time=1).fillna(0)
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

        expected_expr = generator_startup + (1 * generator_status).shift(time=1).fillna(0) <= 1.0
        assert_conequal(expected_expr, actual_constraint.lhs <= actual_constraint.rhs)

    def test_constraint_generator_shutdown_lower_bound(self) -> None:
        actual_constraint = self.linopy_model.constraints["generator_shutdown_lower_bound_constraint"]

        generator_shutdown = self.linopy_model.variables["generator_shutdown"]
        generator_status = self.linopy_model.variables["generator_status"]

        expected_expr = generator_shutdown >= (1 * generator_status).shift(time=1).fillna(0) - generator_status
        assert_conequal(expected_expr, actual_constraint.lhs >= actual_constraint.rhs)

    def test_constraint_generator_shutdown_upper_bound_1(self) -> None:
        actual_constraint = self.linopy_model.constraints["generator_shutdown_upper_bound_1_constraint"]

        generator_shutdown = self.linopy_model.variables["generator_shutdown"]
        generator_status = self.linopy_model.variables["generator_status"]

        expected_expr = generator_shutdown <= (1 * generator_status).shift(time=1).fillna(0)
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
        ).sum() >= self.generator1.min_up_time * (1 * gen1_shutdown).shift(time=-1).fillna(0)
        assert_conequal(gen1_expected_expr, gen1_actual_constraint.lhs >= gen1_actual_constraint.rhs)

        gen2_status = generator_status.sel(generator=self.generator2.name)
        gen2_shutdown = generator_shutdown.sel(generator=self.generator2.name)
        gen2_expected_expr = gen2_status.rolling(
            time=self.generator2.min_up_time,
        ).sum() >= self.generator2.min_up_time * (1 * gen2_shutdown).shift(time=-1).fillna(0)
        assert_conequal(gen2_expected_expr, gen2_actual_constraint.lhs >= gen2_actual_constraint.rhs)

    def test_constraint_generator_min_downtime(self) -> None:
        gen1_constraint_name = f"generator_min_downtime_{self.generator1.name}_constraint"
        gen2_constraint_name = f"generator_min_downtime_{self.generator2.name}_constraint"

        gen1_actual_constraint = self.linopy_model.constraints[gen1_constraint_name]
        gen2_actual_constraint = self.linopy_model.constraints[gen2_constraint_name]

        generator_status = self.linopy_model.variables["generator_status"]
        generator_startup = self.linopy_model.variables["generator_startup"]

        gen1_status = generator_status.sel(generator=self.generator1.name)
        gen1_startup = generator_startup.sel(generator=self.generator1.name)
        gen1_expected_expr = (1 - gen1_status).rolling(
            time=self.generator1.min_down_time,
        ).sum() >= self.generator1.min_down_time * (1 * gen1_startup).shift(time=-1).fillna(0)
        assert_conequal(gen1_expected_expr, gen1_actual_constraint.lhs >= gen1_actual_constraint.rhs)

        gen2_status = generator_status.sel(generator=self.generator2.name)
        gen2_startup = generator_startup.sel(generator=self.generator2.name)
        gen2_expected_expr = (1 - gen2_status).rolling(
            time=self.generator2.min_down_time,
        ).sum() >= self.generator2.min_down_time * (1 * gen2_startup).shift(time=-1).fillna(0)
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

        expected_expr = (generator_power - (1 * generator_power).shift(time=1).fillna(0)).isel(
            time=slice(1, None),
        ) <= max_ramp_up_array
        assert_conequal(expected_expr, actual_constraint.lhs <= actual_constraint.rhs)

    def test_constraint_generator_max_ramp_down(self) -> None:
        actual_constraint = self.linopy_model.constraints["generator_max_ramp_down_constraint"]

        generator_power = self.linopy_model.variables["generator_power"]

        max_ramp_downs = [self.generator1.ramp_down, self.generator2.ramp_down]
        max_ramp_down_array = xr.DataArray(
            max_ramp_downs,
            coords={"generator": [self.generator1.name, self.generator2.name]},
        )

        expected_expr = ((1 * generator_power).shift(time=1).fillna(0) - generator_power).isel(
            time=slice(1, None),
        ) <= max_ramp_down_array
        assert_conequal(expected_expr, actual_constraint.lhs <= actual_constraint.rhs)


class TestGeneratorFormulation:
    @pytest.fixture
    def formulation(
        self,
        optimization_problem: OptimizationProblem,
        linopy_model: linopy.Model,
    ) -> GeneratorFormulation:
        assert linopy_model is not None
        generators = optimization_problem.formulation_of(GeneratorFormulation)
        assert generators is not None
        return generators

    def test_variable_names_match_the_model(self, formulation: GeneratorFormulation) -> None:
        variables = formulation.variables
        assert variables.power.name == GeneratorFormulation.power_name
        assert variables.status.name == GeneratorFormulation.status_name
        assert variables.startup.name == GeneratorFormulation.startup_name
        assert variables.shutdown.name == GeneratorFormulation.shutdown_name

    def test_power_injection_is_the_total_output(
        self,
        formulation: GeneratorFormulation,
        linopy_model: linopy.Model,
    ) -> None:
        expected = linopy_model.variables["generator_power"].sum("generator")
        assert_linequal(formulation.power_injection(), expected)

    def test_profit_is_minus_variable_startup_and_shutdown_cost(
        self,
        formulation: GeneratorFormulation,
        linopy_model: linopy.Model,
        generator1: Generator,
        generator2: Generator,
    ) -> None:
        names = {"generator": [generator1.name, generator2.name]}
        variable_cost = xr.DataArray([generator1.variable_cost, generator2.variable_cost], coords=names)
        startup_cost = xr.DataArray([generator1.startup_cost, generator2.startup_cost], coords=names)
        shutdown_cost = xr.DataArray([generator1.shutdown_cost, generator2.shutdown_cost], coords=names)

        expected = -(
            linopy_model.variables["generator_power"] * HOURS_PER_STEP * variable_cost
            + linopy_model.variables["generator_startup"] * startup_cost
            + linopy_model.variables["generator_shutdown"] * shutdown_cost
        ).sum(["time", "generator"])
        assert_linequal(formulation.profit(), expected)

    def test_variables_before_add_variables_raise(self, optimization_problem: OptimizationProblem) -> None:
        generators = optimization_problem.formulation_of(GeneratorFormulation)
        assert generators is not None
        with pytest.raises(OdysError, match=r"GeneratorFormulation\.add_variables must run before"):
            _ = generators.variables
