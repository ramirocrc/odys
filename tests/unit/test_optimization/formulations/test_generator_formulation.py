"""Unit tests for the generator formulation: variables, constraints, power injection and profit."""

import logging
from datetime import timedelta

import linopy
import pytest
import xarray as xr
from linopy.testing import assert_conequal, assert_linequal

from odys.domain.conditions import GeneratorFinalState, GeneratorInitialState
from odys.domain.entities.fixed_load import FixedLoad
from odys.domain.entities.generator import Generator
from odys.domain.entities.portfolio import AssetPortfolio
from odys.domain.exceptions import OdysError
from odys.domain.profiles import LoadProfile
from odys.domain.scenario import Scenario
from odys.energy_system import EnergySystem
from odys.optimization.formulations.generator import GeneratorFormulation
from odys.optimization.model.model_builder import build_model
from odys.optimization.problem import OptimizationProblem

logger = logging.getLogger(__name__)

HOURS_PER_STEP = 1.0
GEN1_MIN_STEPS = 2
GEN2_MIN_STEPS = 3
GEN1_STEPS_OFF_BEFORE_START = [1.0, 0.0, 0.0]
GEN2_STEPS_OFF_BEFORE_START = [2.0, 1.0, 0.0]
GEN1_INITIAL_POWER = 60.0
GEN2_INITIAL_POWER = 90.0
GEN1_FINAL_POWER = 50.0
GEN1_STEPS_ON_BEFORE_START = [1.0, 0.0, 0.0]
GEN2_STEPS_OFF_CAPPED_BY_TIME_IN_STATE = [1.0, 1.0, 0.0]
NO_STEPS_BEFORE_START = [0.0, 0.0, 0.0]
INITIAL_STATUS = [1.0, 0.0]
FIRST_STEP_ONLY = xr.DataArray([1.0, 0.0, 0.0], coords={"time": ["0", "1", "2"]})
HALF_PROBABILITY = 0.5
ONE_HOUR = timedelta(hours=1)


@pytest.fixture
def generator1() -> Generator:
    """Override conftest generator1 with ramp/min_power/min_up_time/min_down_time params."""
    return Generator(
        name="gen1",
        nominal_power=100.0,
        variable_cost=20.0,
        min_power=10.0,
        min_up_time=timedelta(hours=GEN1_MIN_STEPS),
        min_down_time=timedelta(hours=GEN1_MIN_STEPS),
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
        min_up_time=timedelta(hours=GEN2_MIN_STEPS),
        min_down_time=timedelta(hours=GEN2_MIN_STEPS),
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
    generator1: Generator,
    generator2: Generator,
) -> EnergySystem:
    """Both generators start off, long enough ago that their minimum down time is over."""
    return EnergySystem(
        portfolio=asset_portfolio_sample,
        number_of_steps=len(demand_profile_sample),
        timestep=timedelta(hours=1),
        scenarios=Scenario(profiles=(LoadProfile(load=load1, values=demand_profile_sample),)),
        initial_conditions=(
            GeneratorInitialState(generator=generator1, power=0.0, time_in_state=timedelta(hours=GEN1_MIN_STEPS)),
            GeneratorInitialState(generator=generator2, power=0.0, time_in_state=timedelta(hours=GEN2_MIN_STEPS)),
        ),
    )


def _along_time(values: list[float]) -> xr.DataArray:
    return xr.DataArray(values, coords={"time": [str(t) for t in range(len(values))]})


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
            time=GEN1_MIN_STEPS,
        ).sum() >= GEN1_MIN_STEPS * (1 * gen1_shutdown).shift(time=-1).fillna(0)
        assert_conequal(gen1_expected_expr, gen1_actual_constraint.lhs >= gen1_actual_constraint.rhs)

        gen2_status = generator_status.sel(generator=self.generator2.name)
        gen2_shutdown = generator_shutdown.sel(generator=self.generator2.name)
        gen2_expected_expr = gen2_status.rolling(
            time=GEN2_MIN_STEPS,
        ).sum() >= GEN2_MIN_STEPS * (1 * gen2_shutdown).shift(time=-1).fillna(0)
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
        gen1_expected_expr = (1 - gen1_status).rolling(time=GEN1_MIN_STEPS).sum() + _along_time(
            GEN1_STEPS_OFF_BEFORE_START,
        ) >= GEN1_MIN_STEPS * (1 * gen1_startup).shift(time=-1).fillna(0)
        assert_conequal(gen1_expected_expr, gen1_actual_constraint.lhs >= gen1_actual_constraint.rhs)

        gen2_status = generator_status.sel(generator=self.generator2.name)
        gen2_startup = generator_startup.sel(generator=self.generator2.name)
        gen2_expected_expr = (1 - gen2_status).rolling(time=GEN2_MIN_STEPS).sum() + _along_time(
            GEN2_STEPS_OFF_BEFORE_START,
        ) >= GEN2_MIN_STEPS * (1 * gen2_startup).shift(time=-1).fillna(0)
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

        expected_expr = generator_power - (1 * generator_power).shift(time=1).fillna(0) <= max_ramp_up_array
        assert_conequal(expected_expr, actual_constraint.lhs <= actual_constraint.rhs)

    def test_constraint_generator_max_ramp_down(self) -> None:
        actual_constraint = self.linopy_model.constraints["generator_max_ramp_down_constraint"]

        generator_power = self.linopy_model.variables["generator_power"]

        max_ramp_downs = [self.generator1.ramp_down, self.generator2.ramp_down]
        max_ramp_down_array = xr.DataArray(
            max_ramp_downs,
            coords={"generator": [self.generator1.name, self.generator2.name]},
        )

        expected_expr = (1 * generator_power).shift(time=1).fillna(0) - generator_power <= max_ramp_down_array
        assert_conequal(expected_expr, actual_constraint.lhs <= actual_constraint.rhs)


def _assert_no_masked_entries(constraint: linopy.Constraint) -> None:
    assert bool((constraint.labels != -1).all())


class TestGeneratorFormulationWithInitialAndFinalStates:
    """Two scenarios. Generator 1 starts on, 1 of its 2 minimum up steps done, and has a final power.

    Generator 2 starts off, 1 of its 3 minimum down steps done.
    """

    @pytest.fixture
    def linopy_model(
        self,
        asset_portfolio_sample: AssetPortfolio,
        demand_profile_sample: list[float],
        load1: FixedLoad,
        generator1: Generator,
        generator2: Generator,
    ) -> linopy.Model:
        demand = LoadProfile(load=load1, values=demand_profile_sample)
        energy_system = EnergySystem(
            portfolio=asset_portfolio_sample,
            number_of_steps=len(demand_profile_sample),
            timestep=timedelta(hours=1),
            scenarios=[
                Scenario(name="low", probability=HALF_PROBABILITY, profiles=(demand,)),
                Scenario(name="high", probability=HALF_PROBABILITY, profiles=(demand,)),
            ],
            initial_conditions=(
                GeneratorInitialState(generator=generator1, power=GEN1_INITIAL_POWER, time_in_state=ONE_HOUR),
                GeneratorInitialState(generator=generator2, power=0.0, time_in_state=ONE_HOUR),
            ),
            final_conditions=(GeneratorFinalState(generator=generator1, power=GEN1_FINAL_POWER),),
        )
        return build_model(energy_system.build_problem())

    @staticmethod
    def _along_generators(generator1: Generator, generator2: Generator, values: list[float]) -> xr.DataArray:
        return xr.DataArray(values, coords={"generator": [generator1.name, generator2.name]})

    def _previous_status(
        self,
        linopy_model: linopy.Model,
        generator1: Generator,
        generator2: Generator,
    ) -> linopy.LinearExpression:
        initial_status = self._along_generators(generator1, generator2, INITIAL_STATUS)
        previous: linopy.LinearExpression = (1 * linopy_model.variables["generator_status"]).shift(time=1).fillna(
            0,
        ) + (FIRST_STEP_ONLY * initial_status)
        return previous

    def test_startup_lower_bound_starts_from_the_initial_status(
        self,
        linopy_model: linopy.Model,
        generator1: Generator,
        generator2: Generator,
    ) -> None:
        actual_constraint = linopy_model.constraints["generator_startup_lower_bound_constraint"]
        status = linopy_model.variables["generator_status"]

        expected_expr = linopy_model.variables["generator_startup"] >= status - self._previous_status(
            linopy_model,
            generator1,
            generator2,
        )

        assert_conequal(expected_expr, actual_constraint.lhs >= actual_constraint.rhs)
        _assert_no_masked_entries(actual_constraint)

    def test_startup_upper_bound_2_starts_from_the_initial_status(
        self,
        linopy_model: linopy.Model,
        generator1: Generator,
        generator2: Generator,
    ) -> None:
        actual_constraint = linopy_model.constraints["generator_startup_upper_bound_2_constraint"]

        expected_expr = (
            linopy_model.variables["generator_startup"] + self._previous_status(linopy_model, generator1, generator2)
            <= 1.0
        )

        assert_conequal(expected_expr, actual_constraint.lhs <= actual_constraint.rhs)
        _assert_no_masked_entries(actual_constraint)

    def test_shutdown_lower_bound_starts_from_the_initial_status(
        self,
        linopy_model: linopy.Model,
        generator1: Generator,
        generator2: Generator,
    ) -> None:
        actual_constraint = linopy_model.constraints["generator_shutdown_lower_bound_constraint"]
        status = linopy_model.variables["generator_status"]

        expected_expr = (
            linopy_model.variables["generator_shutdown"]
            >= self._previous_status(linopy_model, generator1, generator2) - status
        )

        assert_conequal(expected_expr, actual_constraint.lhs >= actual_constraint.rhs)
        _assert_no_masked_entries(actual_constraint)

    def test_shutdown_upper_bound_1_starts_from_the_initial_status(
        self,
        linopy_model: linopy.Model,
        generator1: Generator,
        generator2: Generator,
    ) -> None:
        actual_constraint = linopy_model.constraints["generator_shutdown_upper_bound_1_constraint"]

        expected_expr = linopy_model.variables["generator_shutdown"] <= self._previous_status(
            linopy_model,
            generator1,
            generator2,
        )

        assert_conequal(expected_expr, actual_constraint.lhs <= actual_constraint.rhs)
        _assert_no_masked_entries(actual_constraint)

    def test_ramp_up_starts_from_the_initial_power(
        self,
        linopy_model: linopy.Model,
        generator1: Generator,
        generator2: Generator,
    ) -> None:
        actual_constraint = linopy_model.constraints["generator_max_ramp_up_constraint"]
        power = linopy_model.variables["generator_power"]
        initial_power = self._along_generators(generator1, generator2, [GEN1_INITIAL_POWER, 0.0])
        ramp_up = self._along_generators(generator1, generator2, [generator1.ramp_up or 0.0, generator2.ramp_up or 0.0])

        expected_expr = power - (1 * power).shift(time=1).fillna(0) - FIRST_STEP_ONLY * initial_power <= ramp_up

        assert_conequal(expected_expr, actual_constraint.lhs <= actual_constraint.rhs)
        _assert_no_masked_entries(actual_constraint)

    def test_ramp_down_starts_from_the_initial_power(
        self,
        linopy_model: linopy.Model,
        generator1: Generator,
        generator2: Generator,
    ) -> None:
        actual_constraint = linopy_model.constraints["generator_max_ramp_down_constraint"]
        power = linopy_model.variables["generator_power"]
        initial_power = self._along_generators(generator1, generator2, [GEN1_INITIAL_POWER, 0.0])
        ramp_down = self._along_generators(
            generator1,
            generator2,
            [generator1.ramp_down or 0.0, generator2.ramp_down or 0.0],
        )

        expected_expr = (1 * power).shift(time=1).fillna(0) + FIRST_STEP_ONLY * initial_power - power <= ramp_down

        assert_conequal(expected_expr, actual_constraint.lhs <= actual_constraint.rhs)
        _assert_no_masked_entries(actual_constraint)

    @pytest.mark.parametrize(
        ("generator_fixture", "min_steps", "steps_on_before_start"),
        [
            ("generator1", GEN1_MIN_STEPS, GEN1_STEPS_ON_BEFORE_START),
            ("generator2", GEN2_MIN_STEPS, NO_STEPS_BEFORE_START),
        ],
        ids=["on_for_one_step", "off"],
    )
    def test_min_uptime_counts_the_steps_on_before_the_horizon(
        self,
        linopy_model: linopy.Model,
        request: pytest.FixtureRequest,
        generator_fixture: str,
        min_steps: int,
        steps_on_before_start: list[float],
    ) -> None:
        generator: Generator = request.getfixturevalue(generator_fixture)
        actual_constraint = linopy_model.constraints[f"generator_min_uptime_{generator.name}_constraint"]
        status = linopy_model.variables["generator_status"].sel(generator=generator.name)
        shutdown = linopy_model.variables["generator_shutdown"].sel(generator=generator.name)

        expected_expr = status.rolling(time=min_steps).sum() + _along_time(
            steps_on_before_start,
        ) >= min_steps * (1 * shutdown).shift(time=-1).fillna(0)

        assert_conequal(expected_expr, actual_constraint.lhs >= actual_constraint.rhs)
        _assert_no_masked_entries(actual_constraint)

    @pytest.mark.parametrize(
        ("generator_fixture", "min_steps", "steps_off_before_start"),
        [
            ("generator1", GEN1_MIN_STEPS, NO_STEPS_BEFORE_START),
            ("generator2", GEN2_MIN_STEPS, GEN2_STEPS_OFF_CAPPED_BY_TIME_IN_STATE),
        ],
        ids=["on", "off_for_one_step_capped_by_time_in_state"],
    )
    def test_min_downtime_counts_the_steps_off_before_the_horizon(
        self,
        linopy_model: linopy.Model,
        request: pytest.FixtureRequest,
        generator_fixture: str,
        min_steps: int,
        steps_off_before_start: list[float],
    ) -> None:
        generator: Generator = request.getfixturevalue(generator_fixture)
        actual_constraint = linopy_model.constraints[f"generator_min_downtime_{generator.name}_constraint"]
        status = linopy_model.variables["generator_status"].sel(generator=generator.name)
        startup = linopy_model.variables["generator_startup"].sel(generator=generator.name)

        expected_expr = (1 - status).rolling(time=min_steps).sum() + _along_time(
            steps_off_before_start,
        ) >= min_steps * (1 * startup).shift(time=-1).fillna(0)

        assert_conequal(expected_expr, actual_constraint.lhs >= actual_constraint.rhs)
        _assert_no_masked_entries(actual_constraint)

    @pytest.mark.parametrize(
        ("constraint_name", "indicator_name", "generator_fixture"),
        [
            ("generator_initial_min_uptime_constraint", "generator_shutdown", "generator1"),
            ("generator_initial_min_downtime_constraint", "generator_startup", "generator2"),
        ],
        ids=["no_shutdown_while_still_up", "no_startup_while_still_down"],
    )
    def test_initial_min_time_fixes_the_t0_transition_only_for_the_generator_still_within_it(
        self,
        linopy_model: linopy.Model,
        request: pytest.FixtureRequest,
        constraint_name: str,
        indicator_name: str,
        generator_fixture: str,
    ) -> None:
        generator: Generator = request.getfixturevalue(generator_fixture)
        actual_constraint = linopy_model.constraints[constraint_name]
        indicator = linopy_model.variables[indicator_name]

        expected_expr = 1 * indicator.sel(time="0", generator=[generator.name]) == 0

        assert_conequal(expected_expr, actual_constraint.lhs == actual_constraint.rhs)
        _assert_no_masked_entries(actual_constraint)

    def test_final_power_constraint_covers_only_generators_with_a_final_state_in_every_scenario(
        self,
        linopy_model: linopy.Model,
        generator1: Generator,
        demand_profile_sample: list[float],
    ) -> None:
        actual_constraint = linopy_model.constraints["generator_final_power_constraint"]
        last_step = str(len(demand_profile_sample) - 1)
        power = linopy_model.variables["generator_power"]

        expected_expr = power.sel(time=last_step, generator=[generator1.name]) == GEN1_FINAL_POWER

        assert_conequal(expected_expr, actual_constraint.lhs == actual_constraint.rhs)
        assert list(actual_constraint.coords["scenario"].values) == ["low", "high"]
        _assert_no_masked_entries(actual_constraint)


def test_generator_with_min_times_met_and_no_final_state_has_no_initial_min_time_or_final_power_constraints(
    linopy_model: linopy.Model,
) -> None:
    constraint_names = set(linopy_model.constraints)

    assert "generator_initial_min_uptime_constraint" not in constraint_names
    assert "generator_initial_min_downtime_constraint" not in constraint_names
    assert "generator_final_power_constraint" not in constraint_names


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
