import logging
from datetime import timedelta

import linopy
import pytest
import xarray as xr
from linopy.testing import assert_conequal

from odys.domain.entities.flexible_load import FlexibleLoad
from odys.domain.entities.generator import Generator
from odys.domain.entities.market import EnergyMarket
from odys.domain.entities.portfolio import AssetPortfolio
from odys.domain.scenarios import Scenario
from odys.energy_system import EnergySystem

logger = logging.getLogger(__name__)

MAX_INCREASE = 50.0
MAX_DECREASE = 30.0
VALUE_OF_CONSUMPTION = 100.0


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
) -> EnergySystem:
    return EnergySystem(
        portfolio=asset_portfolio_sample,
        markets=market1,
        number_of_steps=len(demand_profile_sample),
        timestep=timedelta(hours=1),
        scenarios=Scenario(
            flexible_load_base_profiles={"flex_load1": demand_profile_sample},
            market_prices={"market1": [50.0, 50.0, 50.0]},
        ),
    )


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
