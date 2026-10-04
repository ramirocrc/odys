"""Unit tests for the flexible-load formulation: variables, constraints, power injection and profit."""

import logging
from datetime import timedelta

import linopy
import pytest
import xarray as xr
from linopy.testing import assert_conequal, assert_linequal

from odys.domain.entities.flexible_load import FlexibleLoad
from odys.domain.entities.generator import Generator
from odys.domain.entities.market import EnergyMarket
from odys.domain.entities.portfolio import AssetPortfolio
from odys.domain.exceptions import OdysError
from odys.domain.profiles import LoadProfile, PriceProfile
from odys.domain.scenario import Scenario
from odys.energy_system import EnergySystem
from odys.optimization.formulations.flexible_load import FlexibleLoadFormulation
from odys.optimization.model.model_builder import build_model
from odys.optimization.problem import OptimizationProblem

logger = logging.getLogger(__name__)

MAX_INCREASE = 50.0
MAX_DECREASE = 30.0
VALUE_OF_CONSUMPTION = 100.0
HOURS_PER_STEP = 1.0


@pytest.fixture
def flexible_load1() -> FlexibleLoad:
    return FlexibleLoad(
        name="flex_load1",
        max_increase=MAX_INCREASE,
        max_decrease=MAX_DECREASE,
        value_of_consumption=VALUE_OF_CONSUMPTION,
    )


@pytest.fixture
def generator1() -> Generator:
    return Generator(name="gen1", nominal_power=200.0, variable_cost=20.0)


@pytest.fixture
def market1() -> EnergyMarket:
    return EnergyMarket(name="market1", max_trading_volume_per_step=1000.0)


@pytest.fixture
def asset_portfolio_sample(
    generator1: Generator,
    flexible_load1: FlexibleLoad,
) -> AssetPortfolio:
    return AssetPortfolio(assets=[generator1, flexible_load1])


@pytest.fixture
def demand_profile_sample() -> list[float]:
    return [100.0, 100.0, 100.0]


@pytest.fixture
def time_index(demand_profile_sample: list[float]) -> list[int]:
    return list(range(len(demand_profile_sample)))


@pytest.fixture
def energy_system_sample(
    asset_portfolio_sample: AssetPortfolio,
    demand_profile_sample: list[float],
    market1: EnergyMarket,
    flexible_load1: FlexibleLoad,
) -> EnergySystem:
    return EnergySystem(
        portfolio=asset_portfolio_sample,
        markets=market1,
        number_of_steps=len(demand_profile_sample),
        timestep=timedelta(hours=1),
        scenarios=Scenario(
            profiles=(
                LoadProfile(load=flexible_load1, values=demand_profile_sample),
                PriceProfile(market=market1, values=[50.0, 50.0, 50.0]),
            ),
        ),
    )


@pytest.fixture
def optimization_problem(energy_system_sample: EnergySystem) -> OptimizationProblem:
    return energy_system_sample.build_problem()


@pytest.fixture
def linopy_model(optimization_problem: OptimizationProblem) -> linopy.Model:
    return build_model(optimization_problem).linopy_model


@pytest.fixture
def formulation(optimization_problem: OptimizationProblem, linopy_model: linopy.Model) -> FlexibleLoadFormulation:
    """The flexible-load formulation of a built model (its variables exist)."""
    assert linopy_model is not None
    flexible_loads = optimization_problem.formulation_of(FlexibleLoadFormulation)
    assert flexible_loads is not None
    return flexible_loads


class TestFlexibleLoadConstraints:
    @pytest.fixture(autouse=True)
    def setup(
        self,
        linopy_model: linopy.Model,
        flexible_load1: FlexibleLoad,
        time_index: list[int],
    ) -> None:
        self.linopy_model = linopy_model
        self.flexible_load1 = flexible_load1
        self.time_index = time_index

    def test_adjustment_lower_bound(self) -> None:
        actual_constraint = self.linopy_model.constraints["flexible_load_adjustment_lower_bound_constraint"]

        load_adjustment = self.linopy_model.variables["load_adjustment"]
        max_decrease_array = xr.DataArray(
            [self.flexible_load1.max_decrease],
            coords={"flexible_load": [self.flexible_load1.name]},
        )

        expected_expr = load_adjustment >= -max_decrease_array
        assert_conequal(expected_expr, actual_constraint.lhs >= actual_constraint.rhs)

    def test_adjustment_upper_bound(self) -> None:
        actual_constraint = self.linopy_model.constraints["flexible_load_adjustment_upper_bound_constraint"]

        load_adjustment = self.linopy_model.variables["load_adjustment"]
        max_increase_array = xr.DataArray(
            [self.flexible_load1.max_increase],
            coords={"flexible_load": [self.flexible_load1.name]},
        )

        expected_expr = load_adjustment <= max_increase_array
        assert_conequal(expected_expr, actual_constraint.lhs <= actual_constraint.rhs)


class TestFlexibleLoadFormulation:
    def test_variables_before_add_variables_raise(self, optimization_problem: OptimizationProblem) -> None:
        flexible_loads = optimization_problem.formulation_of(FlexibleLoadFormulation)
        assert flexible_loads is not None
        with pytest.raises(OdysError, match="add_variables must run before its variables are used"):
            _ = flexible_loads.variables

    def test_load_adjustment_is_unbounded_over_scenario_time_and_load(
        self,
        formulation: FlexibleLoadFormulation,
        linopy_model: linopy.Model,
    ) -> None:
        load_adjustment = linopy_model.variables["load_adjustment"]

        assert formulation.variables.load_adjustment.name == FlexibleLoadFormulation.variable_name
        assert load_adjustment.dims == ("scenario", "time", "flexible_load")
        assert bool((load_adjustment.lower == -float("inf")).all())

    def test_power_injection_is_minus_base_profile_and_adjustment(
        self,
        formulation: FlexibleLoadFormulation,
        linopy_model: linopy.Model,
        demand_profile_sample: list[float],
    ) -> None:
        load_adjustment = linopy_model.variables["load_adjustment"]
        base_profile = xr.DataArray(
            [demand_profile_sample],
            coords={"scenario": ["base"], "time": ["0", "1", "2"]},
        )

        expected = -load_adjustment.sum("flexible_load") - base_profile
        assert_linequal(formulation.power_injection(), expected)

    def test_profit_values_the_adjustment_per_step(
        self,
        formulation: FlexibleLoadFormulation,
        linopy_model: linopy.Model,
        flexible_load1: FlexibleLoad,
    ) -> None:
        load_adjustment = linopy_model.variables["load_adjustment"]
        value_of_consumption = xr.DataArray(
            [flexible_load1.value_of_consumption],
            coords={"flexible_load": [flexible_load1.name]},
        )

        expected = (load_adjustment * HOURS_PER_STEP * value_of_consumption).sum(["time", "flexible_load"])
        assert_linequal(formulation.profit(), expected)
