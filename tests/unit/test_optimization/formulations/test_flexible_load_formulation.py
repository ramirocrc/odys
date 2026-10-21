"""Unit tests for the flexible-load formulation: variables, constraints, power injection and profit."""

import logging
from datetime import timedelta

import linopy
import pytest
import xarray as xr
from linopy.testing import assert_conequal, assert_linequal

from odys.domain.conditions import FlexibleLoadInitialState
from odys.domain.entities.commitment import Commitment
from odys.domain.entities.flexible_load import FlexibleLoad
from odys.domain.entities.generator import Generator
from odys.domain.entities.market import EnergyMarket
from odys.domain.entities.portfolio import AssetPortfolio
from odys.domain.exceptions import OdysError
from odys.domain.profiles import FlexibleLoadProfile, PriceProfile
from odys.domain.scenario import Scenario
from odys.energy_system import EnergySystem
from odys.optimization.formulations.flexible_load import FlexibleLoadFormulation
from odys.optimization.model.model_builder import build_model
from odys.optimization.problem import OptimizationProblem

logger = logging.getLogger(__name__)

LOWER_BOUND = (70.0, 80.0, 60.0)
UPPER_BOUND = (150.0, 120.0, 130.0)
SECOND_LOWER_BOUND = (10.0, 10.0, 10.0)
SECOND_UPPER_BOUND = (20.0, 25.0, 30.0)
VALUE_OF_CONSUMPTION = 100.0
HOURS_PER_STEP = 1.0
PRICES = (50.0, 50.0, 50.0)
TIME = ["0", "1", "2"]


@pytest.fixture
def flexible_load1() -> FlexibleLoad:
    return FlexibleLoad(name="flex_load1", value_of_consumption=VALUE_OF_CONSUMPTION)


@pytest.fixture
def flexible_load2() -> FlexibleLoad:
    return FlexibleLoad(name="flex_load2", value_of_consumption=VALUE_OF_CONSUMPTION)


@pytest.fixture
def generator1() -> Generator:
    return Generator(name="gen1", nominal_power=200.0, variable_cost=20.0)


@pytest.fixture
def market1() -> EnergyMarket:
    return EnergyMarket(name="market1", max_trading_volume_per_step=1000.0)


@pytest.fixture
def energy_system_sample(
    generator1: Generator,
    flexible_load1: FlexibleLoad,
    flexible_load2: FlexibleLoad,
    market1: EnergyMarket,
) -> EnergySystem:
    return EnergySystem(
        portfolio=AssetPortfolio(assets=[generator1, flexible_load1, flexible_load2]),
        markets=market1,
        number_of_steps=len(LOWER_BOUND),
        timestep=timedelta(hours=1),
        scenarios=Scenario(
            profiles=(
                FlexibleLoadProfile(load=flexible_load1, lower_bound=LOWER_BOUND, upper_bound=UPPER_BOUND),
                FlexibleLoadProfile(
                    load=flexible_load2,
                    lower_bound=SECOND_LOWER_BOUND,
                    upper_bound=SECOND_UPPER_BOUND,
                ),
                PriceProfile(market=market1, values=PRICES),
            ),
        ),
    )


@pytest.fixture
def optimization_problem(energy_system_sample: EnergySystem) -> OptimizationProblem:
    return energy_system_sample.build_problem()


@pytest.fixture
def linopy_model(optimization_problem: OptimizationProblem) -> linopy.Model:
    return build_model(optimization_problem)


@pytest.fixture
def formulation(optimization_problem: OptimizationProblem, linopy_model: linopy.Model) -> FlexibleLoadFormulation:
    """The flexible-load formulation of a built model (its variables exist)."""
    assert linopy_model is not None
    flexible_loads = optimization_problem.formulation_of(FlexibleLoadFormulation)
    assert flexible_loads is not None
    return flexible_loads


def _bounds(first: tuple[float, ...], second: tuple[float, ...]) -> xr.DataArray:
    return xr.DataArray(
        [list(zip(first, second, strict=True))],
        coords={"scenario": ["base"], "time": TIME, "flexible_load": ["flex_load1", "flex_load2"]},
    )


class TestFlexibleLoadConstraints:
    def test_lower_bound_constraint_keeps_consumption_at_or_above_the_profile_lower_bound(
        self,
        linopy_model: linopy.Model,
    ) -> None:
        actual_constraint = linopy_model.constraints["flexible_load_lower_bound_constraint"]
        consumption = linopy_model.variables[FlexibleLoadFormulation.variable_name]

        expected_expr = consumption >= _bounds(LOWER_BOUND, SECOND_LOWER_BOUND)
        assert_conequal(expected_expr, actual_constraint.lhs >= actual_constraint.rhs)
        assert bool((actual_constraint.labels != -1).all())

    def test_upper_bound_constraint_keeps_consumption_at_or_below_the_profile_upper_bound(
        self,
        linopy_model: linopy.Model,
    ) -> None:
        actual_constraint = linopy_model.constraints["flexible_load_upper_bound_constraint"]
        consumption = linopy_model.variables[FlexibleLoadFormulation.variable_name]

        expected_expr = consumption <= _bounds(UPPER_BOUND, SECOND_UPPER_BOUND)
        assert_conequal(expected_expr, actual_constraint.lhs <= actual_constraint.rhs)
        assert bool((actual_constraint.labels != -1).all())


class TestFlexibleLoadFormulation:
    def test_variables_before_add_variables_raise(self, optimization_problem: OptimizationProblem) -> None:
        flexible_loads = optimization_problem.formulation_of(FlexibleLoadFormulation)
        assert flexible_loads is not None
        with pytest.raises(OdysError, match="add_variables must run before its variables are used"):
            _ = flexible_loads.variables

    def test_consumption_is_non_negative_over_scenario_time_and_load(
        self,
        formulation: FlexibleLoadFormulation,
        linopy_model: linopy.Model,
    ) -> None:
        consumption = linopy_model.variables["flexible_load_consumption"]

        assert formulation.variables.consumption.name == FlexibleLoadFormulation.variable_name
        assert consumption.dims == ("scenario", "time", "flexible_load")
        assert bool((consumption.lower == 0).all())

    def test_power_injection_is_minus_the_summed_consumption(
        self,
        formulation: FlexibleLoadFormulation,
        linopy_model: linopy.Model,
    ) -> None:
        consumption = linopy_model.variables[FlexibleLoadFormulation.variable_name]

        assert_linequal(formulation.power_injection(), -consumption.sum("flexible_load"))

    def test_profit_values_the_consumption_per_step(
        self,
        formulation: FlexibleLoadFormulation,
        linopy_model: linopy.Model,
    ) -> None:
        consumption = linopy_model.variables[FlexibleLoadFormulation.variable_name]
        value_of_consumption = xr.DataArray(
            [VALUE_OF_CONSUMPTION, VALUE_OF_CONSUMPTION],
            coords={"flexible_load": ["flex_load1", "flex_load2"]},
        )

        expected = (consumption * HOURS_PER_STEP * value_of_consumption).sum(["time", "flexible_load"])
        assert_linequal(formulation.profit(), expected)


@pytest.mark.parametrize(
    "name",
    [FlexibleLoadFormulation.status_name, FlexibleLoadFormulation.startup_name, FlexibleLoadFormulation.shutdown_name],
)
def test_flexible_loads_without_a_commitment_add_no_on_off_variables(linopy_model: linopy.Model, name: str) -> None:
    assert name not in set(linopy_model.variables)


KILN_LOWER_BOUND = (30.0, 30.0, 30.0)
KILN_UPPER_BOUND = (90.0, 80.0, 90.0)
PUMP_BOUNDS = (5.0, 5.0, 5.0)
KILN_RAMP_UP = 20.0
KILN_RAMP_DOWN = 40.0
KILN_INITIAL_POWER = 60.0
STARTUP_COST = 500.0
SHUTDOWN_COST = 100.0
HOURS_PER_HALF_HOUR = 0.5
FIRST_STEP_ONLY = xr.DataArray([1.0, 0.0, 0.0], coords={"time": TIME})
KILN = {"flexible_load": "kiln"}
PUMP = {"flexible_load": "pump"}


class TestSwitchableRampingFlexibleLoad:
    """Half-hourly steps. The kiln has ramps and a commitment, and starts at 60 MW; the pump is always on."""

    @pytest.fixture
    def linopy_model(self, market1: EnergyMarket) -> linopy.Model:
        kiln = FlexibleLoad(
            name="kiln",
            value_of_consumption=VALUE_OF_CONSUMPTION,
            ramp_up=KILN_RAMP_UP,
            ramp_down=KILN_RAMP_DOWN,
            commitment=Commitment(
                min_up_time=timedelta(hours=1),
                startup_cost=STARTUP_COST,
                shutdown_cost=SHUTDOWN_COST,
            ),
        )
        pump = FlexibleLoad(name="pump", value_of_consumption=VALUE_OF_CONSUMPTION)
        system = EnergySystem(
            portfolio=AssetPortfolio(assets=[kiln, pump]),
            markets=market1,
            number_of_steps=len(TIME),
            timestep=timedelta(minutes=30),
            scenarios=Scenario(
                profiles=(
                    FlexibleLoadProfile(load=kiln, lower_bound=KILN_LOWER_BOUND, upper_bound=KILN_UPPER_BOUND),
                    FlexibleLoadProfile(load=pump, lower_bound=PUMP_BOUNDS, upper_bound=PUMP_BOUNDS),
                    PriceProfile(market=market1, values=PRICES),
                ),
            ),
            initial_conditions=(
                FlexibleLoadInitialState(load=kiln, power=KILN_INITIAL_POWER, time_in_state=timedelta(hours=2)),
            ),
        )
        return build_model(system.build_problem())

    @staticmethod
    def _bounds(kiln: tuple[float, ...], pump: tuple[float, ...]) -> xr.DataArray:
        return xr.DataArray(
            [list(zip(kiln, pump, strict=True))],
            coords={"scenario": ["base"], "time": TIME, "flexible_load": ["kiln", "pump"]},
        )

    def test_range_applies_only_while_running(self, linopy_model: linopy.Model) -> None:
        consumption = linopy_model.variables[FlexibleLoadFormulation.variable_name]
        status = linopy_model.variables[FlexibleLoadFormulation.status_name]
        lower = linopy_model.constraints["flexible_load_lower_bound_constraint"]
        upper = linopy_model.constraints["flexible_load_upper_bound_constraint"]

        assert_conequal(consumption >= status * self._bounds(KILN_LOWER_BOUND, PUMP_BOUNDS), lower.lhs >= lower.rhs)
        assert_conequal(consumption <= status * self._bounds(KILN_UPPER_BOUND, PUMP_BOUNDS), upper.lhs <= upper.rhs)

    def test_load_without_a_commitment_is_always_on(self, linopy_model: linopy.Model) -> None:
        actual_constraint = linopy_model.constraints["flexible_load_always_on_constraint"]
        status = linopy_model.variables[FlexibleLoadFormulation.status_name]

        expected = (1 * status.sel({"flexible_load": ["pump"]})).to_constraint("=", 1)
        assert_conequal(expected, actual_constraint.lhs == actual_constraint.rhs)
        _assert_no_masked_entries(actual_constraint)

    def test_ramp_up_is_per_hour_from_the_initial_power_and_free_at_a_start(self, linopy_model: linopy.Model) -> None:
        actual_constraint = linopy_model.constraints["flexible_load_max_ramp_up_constraint"]
        consumption = linopy_model.variables[FlexibleLoadFormulation.variable_name].sel(KILN)
        startup = linopy_model.variables[FlexibleLoadFormulation.startup_name].sel(KILN)
        upper_bound = xr.DataArray(list(KILN_UPPER_BOUND), coords={"time": TIME})

        increase = consumption - (1 * consumption).shift(time=1).fillna(0) - FIRST_STEP_ONLY * KILN_INITIAL_POWER
        expected = increase - startup * upper_bound <= KILN_RAMP_UP * HOURS_PER_HALF_HOUR
        assert_conequal(expected, actual_constraint.lhs.sel(KILN) <= actual_constraint.rhs.sel(KILN))
        assert list(actual_constraint.labels.coords["flexible_load"].values) == ["kiln"]
        _assert_no_masked_entries(actual_constraint)

    def test_ramp_down_is_per_hour_from_the_initial_power_and_free_at_a_stop(self, linopy_model: linopy.Model) -> None:
        actual_constraint = linopy_model.constraints["flexible_load_max_ramp_down_constraint"]
        consumption = linopy_model.variables[FlexibleLoadFormulation.variable_name].sel(KILN)
        shutdown = linopy_model.variables[FlexibleLoadFormulation.shutdown_name].sel(KILN)
        previous_upper_bound = xr.DataArray([KILN_INITIAL_POWER, *KILN_UPPER_BOUND[:-1]], coords={"time": TIME})

        decrease = (1 * consumption).shift(time=1).fillna(0) + FIRST_STEP_ONLY * KILN_INITIAL_POWER - consumption
        expected = decrease - shutdown * previous_upper_bound <= KILN_RAMP_DOWN * HOURS_PER_HALF_HOUR
        assert_conequal(expected, actual_constraint.lhs.sel(KILN) <= actual_constraint.rhs.sel(KILN))
        _assert_no_masked_entries(actual_constraint)

    @pytest.mark.parametrize(
        "name",
        [
            "flexible_load_startup_lower_bound_constraint",
            "flexible_load_shutdown_upper_bound_2_constraint",
            "flexible_load_min_uptime_kiln_constraint",
            "flexible_load_min_downtime_pump_constraint",
        ],
    )
    def test_on_off_rules_are_shared_with_generators_under_the_flexible_load_prefix(
        self,
        linopy_model: linopy.Model,
        name: str,
    ) -> None:
        assert name in set(linopy_model.constraints)

    def test_profit_subtracts_startup_and_shutdown_costs(self, linopy_model: linopy.Model) -> None:
        objective = linopy_model.objective.expression
        startup = linopy_model.variables[FlexibleLoadFormulation.startup_name].sel(KILN)
        shutdown = linopy_model.variables[FlexibleLoadFormulation.shutdown_name].sel(KILN)

        coefficients = dict(zip(objective.vars.values.ravel(), objective.coeffs.values.ravel(), strict=True))

        assert all(coefficients[label] == pytest.approx(-STARTUP_COST) for label in startup.labels.values.ravel())
        assert all(coefficients[label] == pytest.approx(-SHUTDOWN_COST) for label in shutdown.labels.values.ravel())


def _assert_no_masked_entries(constraint: linopy.Constraint) -> None:
    assert bool((constraint.labels != -1).all())


def test_ramp_down_of_a_load_without_a_commitment_has_no_shutdown_term(market1: EnergyMarket) -> None:
    pump = FlexibleLoad(name="pump", value_of_consumption=VALUE_OF_CONSUMPTION, ramp_down=KILN_RAMP_DOWN)
    system = EnergySystem(
        portfolio=AssetPortfolio(assets=[pump]),
        markets=market1,
        number_of_steps=len(TIME),
        timestep=timedelta(minutes=30),
        scenarios=Scenario(
            profiles=(
                FlexibleLoadProfile(load=pump, lower_bound=KILN_LOWER_BOUND, upper_bound=KILN_UPPER_BOUND),
                PriceProfile(market=market1, values=PRICES),
            ),
        ),
        initial_conditions=(FlexibleLoadInitialState(load=pump, power=KILN_INITIAL_POWER),),
    )
    linopy_model = build_model(system.build_problem())
    actual_constraint = linopy_model.constraints["flexible_load_max_ramp_down_constraint"]
    consumption = linopy_model.variables[FlexibleLoadFormulation.variable_name]

    decrease = (1 * consumption).shift(time=1).fillna(0) + FIRST_STEP_ONLY * KILN_INITIAL_POWER - consumption
    assert_conequal(decrease <= KILN_RAMP_DOWN * HOURS_PER_HALF_HOUR, actual_constraint.lhs <= actual_constraint.rhs)
    _assert_no_masked_entries(actual_constraint)
